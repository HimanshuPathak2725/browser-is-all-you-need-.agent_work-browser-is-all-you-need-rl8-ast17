# GPT-5.6 Luna via OpenRouter: clean-room Aider fixed-26 evaluation

This runner evaluates the pinned Aider Polyglot C++ fixed-26 benchmark against
OpenRouter model `openai/gpt-5.6-luna` without exposing historical training or
evaluation data to the model. The user-facing runner argument remains
`--model gpt-5.6-luna`; the validating proxy alone converts it to OpenRouter's
namespaced model slug.

Literal zero network access is incompatible with a hosted model. The runtime
network contract is therefore:

```text
pinned image build -> one fresh Sandbox per task -> openrouter.ai:443 only
                              |
                              +-- no volumes or bucket mounts
                              +-- no tools, browser, MCP, files, or response state
                              +-- current task only
                              +-- C++ build/test with no socket syscalls
                              v
                      Sandbox process exits
                              v
                 controller downloads and terminates Sandbox
                              v
                       new local result directory
```

The inference Sandbox never mounts `/runs`, `/results`, `/assets`, `/models`,
the post-training workspace, W&B data, or a previous evaluation. The local
controller publishes a new result directory only after all inference processes
have exited and their Sandboxes have been terminated.

## 1. Evaluation contracts

Run pass@1 and repair/pass@2 as independent jobs:

| Job | `--tries` | Previous information permitted in a model request |
| --- | ---: | --- |
| Luna pass@1 | 1 | None |
| Luna repair/pass@2 | 2 | Only attempt 1 and test feedback from the same task in the same job |

The pass@2 job starts new Sandboxes and a fresh copy of every task. It does not
read the pass@1 output. A matching preflight receipt is checked by the local
controller but is never copied into an inference Sandbox or an API request.

## 2. Install a Modal client with domain allowlists

Domain allowlists were added in Modal 1.5.0. The runner deliberately refuses to
fall back to unrestricted egress when an older SDK is installed.

```bash
cd /data/Tirtha/browser-is-all-you-need/.agent_work/browser-is-all-you-need-rl8-ast17

python3 -m pip install --upgrade 'modal>=1.5.0,<2'
python3 -c 'import inspect, modal; print(modal.__version__); print("outbound_domain_allowlist" in inspect.signature(modal.Sandbox.create).parameters)'
```

The second command must print `True`.

Modal's domain allowlist permits TLS only to the named domains and blocks other
destinations. See [Modal Sandbox networking](https://modal.com/docs/guide/sandbox-networking).

## 3. Create the dedicated OpenRouter secret

The W&B secret is not used by this evaluator. Enter the OpenRouter key without
putting it in source code, a tracked `.env` file, W&B, or a receipt:

```zsh
read -s "OPENROUTER_API_KEY?OpenRouter API key: "
echo
modal secret create --force openrouter-api \
  OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
unset OPENROUTER_API_KEY

modal secret list --json
```

Inspect only the secret metadata. Do not print or retrieve the value.

Before any paid preflight, configure a hard spending limit for the dedicated
key in OpenRouter. A `null` limit means the key has no key-level cap. The
read-only endpoint below verifies the key metadata without making an inference
request; do not print or archive any credential:

```zsh
curl -sS https://openrouter.ai/api/v1/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '{is_free_tier: .data.is_free_tier, limit: .data.limit, limit_remaining: .data.limit_remaining, expires_at: .data.expires_at}'
```

If a key was ever pasted into chat, logs, or another non-secret channel, rotate
it and overwrite `openrouter-api` before running the evaluation.

## 4. Run local static tests

```bash
pytest -q tests/test_aider_api_cleanroom_eval.py
python3 -m py_compile \
  examples/modal/aider_api_base_eval_app.py \
  scripts/aider_cleanroom_runtime.py \
  scripts/prepare_aider_cleanroom_image.py
```

## 5. What the immutable image contains

The first Modal launch builds a CPU-only image from a digest-pinned Python base
and installs:

- Aider commit `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`.
- Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`.
- Aider's fully resolved `requirements.txt` at that commit.
- `cmake`, `make`, `g++`, Bubblewrap, and a tiny seccomp launcher.
- Only the four clean-room runtime/image-finalization files explicitly added
  by `examples/modal/aider_api_base_eval_app.py`.

The build removes both `.git` directories, rejects historical result/adapter
filenames, records Git tree IDs, records Python and Debian package manifests,
and replaces only two benchmark details:

1. A fixed receipt commit string replaces the runtime `.git` lookup.
2. The C++ test script runs under Bubblewrap with `env -i` and a minimal
   filesystem. A fail-closed seccomp launcher denies `socket` and `socketpair`
   for the build, test binary, and all descendants. This is used instead of a
   nested network namespace because Modal's gVisor runtime rejects Bubblewrap's
   nested loopback setup.

The runtime also removes the selected task's `.meta/example*` ground-truth
files before Aider starts. Aider receives only the task instructions and its
starter solution files. Test and other-task filenames are checked at the API
proxy boundary, except when the pinned current-task instructions already name
a test file while defining the public interface. That intentional filename is
recorded in the task receipt; the test file and its contents are still absent
from the model input.

## 6. Run the pass@1 preflight

The preflight builds the image, checks filesystem and network isolation, runs a
known-good and known-bad C++ project, executes a small API compatibility probe,
and evaluates two Luna tasks with `tries=1`.

```bash
cd /data/Tirtha/browser-is-all-you-need/.agent_work/browser-is-all-you-need-rl8-ast17

export LUNA_OUTPUT_ROOT="$PWD/artifacts/luna-cleanroom-evals"
export LUNA_PASS1_PREFLIGHT_RUN_ID="gpt56-luna-pass1-preflight-$(date -u +%Y%m%dT%H%M%SZ)"

modal run examples/modal/aider_api_base_eval_app.py \
  --model gpt-5.6-luna \
  --tries 1 \
  --reasoning-effort medium \
  --preflight \
  --max-parallel 2 \
  --output-root "$LUNA_OUTPUT_ROOT" \
  --run-id "$LUNA_PASS1_PREFLIGHT_RUN_ID"

export LUNA_PASS1_PREFLIGHT_RECEIPT="$LUNA_OUTPUT_ROOT/$LUNA_PASS1_PREFLIGHT_RUN_ID/run_receipt.json"
test -f "$LUNA_PASS1_PREFLIGHT_RECEIPT"
```

Do not add `--detach`: the local controller must download each new task bundle
and terminate its Sandbox before publishing the run directory.

The worker atomically publishes a completed archive and a manifest containing
its exact byte size and SHA-256. The controller rereads until size, checksum,
gzip, and tar validation all pass, then sends `ack_verified` and persists that
task immediately. It never terminates a worker based on a merely non-empty
read, and a later task failure cannot discard already downloaded evidence.
The full-run gate also compares the preflight's controller/runtime source-file
hashes with the current files, so any protocol change requires a fresh
preflight.

The preflight aborts if any of these checks fail:

- `/runs`, `/results`, `/assets`, `/models`, or `/workspace` exists.
- A historical result, adapter, rollout, W&B directory, or Git checkout exists.
- `github.com`, `huggingface.co`, or `wandb.ai` is reachable.
- `openrouter.ai` or the exact `openai/gpt-5.6-luna` model is unavailable.
- Direct access to `api.openai.com` is unexpectedly possible.
- Bubblewrap cannot compile/run known-good C++ without network access.
- Invalid C++ is not rejected.
- The candidate inherits a secret-bearing environment.
- An outbound serialized API request lacks `store: false`, explicit `reasoning_effort`,
  or `max_completion_tokens: 32768`.
- A serialized request contains tools or state IDs.
- A hidden/other-task filename not already disclosed by the pinned current-task
  instructions, or a historical-run marker, reaches the prompt.

## 7. Run the independent full pass@1 job

```bash
export LUNA_PASS1_RUN_ID="gpt56-luna-base-pass1-$(date -u +%Y%m%dT%H%M%SZ)"

modal run examples/modal/aider_api_base_eval_app.py \
  --model gpt-5.6-luna \
  --tries 1 \
  --reasoning-effort medium \
  --preflight-receipt "$LUNA_PASS1_PREFLIGHT_RECEIPT" \
  --max-parallel 4 \
  --output-root "$LUNA_OUTPUT_ROOT" \
  --run-id "$LUNA_PASS1_RUN_ID"
```

Each of the 26 tasks gets a separate no-volume Sandbox. No task transcript is
reused by another task.

## 8. Run pass@2 as a separate job

Pass@2 needs its own tries=2 preflight because its information contract differs
from pass@1:

```bash
export LUNA_PASS2_PREFLIGHT_RUN_ID="gpt56-luna-pass2-preflight-$(date -u +%Y%m%dT%H%M%SZ)"

modal run examples/modal/aider_api_base_eval_app.py \
  --model gpt-5.6-luna \
  --tries 2 \
  --reasoning-effort medium \
  --preflight \
  --max-parallel 2 \
  --output-root "$LUNA_OUTPUT_ROOT" \
  --run-id "$LUNA_PASS2_PREFLIGHT_RUN_ID"

export LUNA_PASS2_PREFLIGHT_RECEIPT="$LUNA_OUTPUT_ROOT/$LUNA_PASS2_PREFLIGHT_RUN_ID/run_receipt.json"
export LUNA_PASS2_RUN_ID="gpt56-luna-base-repair-$(date -u +%Y%m%dT%H%M%SZ)"

modal run examples/modal/aider_api_base_eval_app.py \
  --model gpt-5.6-luna \
  --tries 2 \
  --reasoning-effort medium \
  --preflight-receipt "$LUNA_PASS2_PREFLIGHT_RECEIPT" \
  --max-parallel 4 \
  --output-root "$LUNA_OUTPUT_ROOT" \
  --run-id "$LUNA_PASS2_RUN_ID"
```

Attempt 2 can see only its own task's attempt-1 edit and compiler/test feedback,
which is the Aider repair contract. The entire pass@2 run is fresh and cannot
read pass@1 results.

## 9. Evidence layout

Every completed run is written to a previously nonexistent local directory:

```text
artifacts/luna-cleanroom-evals/<run-id>/
  run_receipt.json
  publication_receipt.json
  run_bundle.tar.gz
  raw-task-bundles/<task>.tar.gz
  controller-logs/<task>.stdout.txt
  controller-logs/<task>.stderr.txt
  tasks/<task>/
    task_receipt.json
    request_receipts.jsonl
    benchmark.command.json
    benchmark.stdout.txt
    benchmark.stderr.txt
    benchmark.stats.txt
    benchmark-output/...
```

Request receipts contain prompt and response hashes, role sequences, parameter
names, model IDs, isolation booleans, and token usage. They deliberately do not
contain the API key or duplicate raw prompt text. Current-task completions and
test evidence remain in the normal Aider task output and chat history.

The merged receipt distinguishes `pass_at_1` from `pass_at_k`, and records
well-formed, malformed, error, context-exhaustion, timeout, prompt-token,
completion-token, and reasoning-token totals.

## 10. OpenRouter request and retention boundary

The local proxy forwards only Chat Completions requests that contain:

- Exact OpenRouter model `openai/gpt-5.6-luna`.
- Explicit `reasoning_effort` (initially `medium`).
- Explicit `store: false`.
- Exact `max_completion_tokens: 32768` for benchmark calls.
- Current-task messages only.
- `provider.zdr: true`.
- `provider.data_collection: deny`.
- `provider.require_parameters: true`.

It removes only null state/tool fields and rejects any populated tool, function,
conversation, file, vector-store, MCP, web-search, or previous-response field.

Pinned Aider/LiteLLM may omit a false-valued `store` field when it calls the
local trusted proxy. The proxy records this omission, injects `store: false`
into the exact upstream body, and rejects every explicitly supplied non-false
value. Thus the request sent to OpenRouter always contains `store: false`.
It never forwards the local proxy credential; only the proxy process retains
the real OpenRouter key in memory. Modal permits TLS egress only to
`openrouter.ai`, and direct connections to OpenAI, GitHub, Hugging Face, and
W&B are explicitly checked as blocked.

OpenAI documents `reasoning_effort`, `max_completion_tokens`, and `store` on the
[Chat Completions create endpoint](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
The GPT-5.6 model guide identifies Luna and its supported reasoning controls in
[GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/model-guidance?model=gpt-5.6).

OpenRouter documents the `openai/gpt-5.6-luna` slug and OpenAI-compatible Chat
Completions endpoint in its [model catalog](https://openrouter.ai/openai/gpt-5.6-luna-20260709)
and [quickstart](https://openrouter.ai/docs/quickstart). The proxy requires
per-request ZDR and rejects provider routing supplied by Aider; see
[OpenRouter ZDR](https://openrouter.ai/docs/guides/features/zdr). Also verify in
the OpenRouter dashboard that private input/output logging and use of
inputs/outputs are disabled. `store: false` remains part of the upstream OpenAI
request contract, but it is not by itself a complete cross-provider retention
guarantee.

This setup proves that local historical runs were unavailable to the inference
workers and absent from serialized requests. It cannot prove that a hosted
model was never pretrained on publicly available benchmark material.
