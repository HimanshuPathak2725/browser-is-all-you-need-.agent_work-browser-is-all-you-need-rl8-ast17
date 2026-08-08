# SynthMem-v1 epoch-50 thinking-on public-PR evaluation

This is the current one-task GCP lane. It preserves the compact best-of-four
compiler-repair prompt and evaluator while replacing the served adapter with the
genuine SynthMem-v1 epoch-50 checkpoint. Historical v2-v4 contracts and the
SynthMem-v3 profile remain unchanged.

The run is fail-closed:

- checkpoint profile: `synthmem-v1-ep50`;
- parent run: `glm47-synth-memorization-v1-100ep-20260731T071000Z`;
- checkpoint: `checkpoints/sft_lora_r16/iter_0000649`;
- source adapter SHA-256:
  `4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a`;
- converted serving adapter SHA-256:
  `6de1aeba533a5bfef26a73286fc32b47f403c022bd7467e2b3dc32cf18a35f48`;
- adapter config SHA-256:
  `0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e`;
- base model revision:
  `7dd20894a642a0aa287e9827cb1a1f7f91386b67`;
- task contract:
  `public-pr-repo-eval-demo-fmtlib-v6.jsonl`;
- task contract SHA-256:
  `a8c59421d38ea2dbdf0bca6168398c590d9497cdd0acdbced9d0377c8725746f`;
- suite: `fmtlib-verified-mechanisms-thinking`;
- request setting:
  `chat_template_kwargs.enable_thinking=true`.

The runtime records the checkpoint identity, adapter conversion hashes, thinking
request contract, and exact per-seed model-settings files. The dedicated image
prepares only v6, so image construction performs one oracle replay rather than
building the historical full, v2, v3, and v4 suites.

## Compile-gated mechanism reporting

The v6 lane does not treat substring matches or upstream-patch similarity as a
correctness score. Every attempt reports three separate layers:

- **Textual hints**: raw required/forbidden token hints, diagnostic only.
- **Structurally valid**: tokenized preprocessor, namespace, declaration,
  template/overload, and call-site checks, still diagnostic only.
- **Executable verified**: a named mechanism counts only when its structure is
  valid, the mandatory compile matrix passes, and its focused probe passes.

If any mandatory compile gate fails, the receipt reports
`verified_mechanisms.status=unavailable` with
`reason=compile_gate_failed`; it never presents an uncompilable candidate as a
partial verified x/12. The final result also requires the ordinary chrono test
and independent probe. Textual or structural evidence cannot override it.

The mandatory matrix is GCC 13 C++11 with `FMT_SAFE_DURATION_CAST=1`, GCC 13
C++11 with it set to `0`, `-Wall -Wextra -Werror`, and a C++11 UBSan build.
Each non-local mechanism executes independently under safe-on, safe-off, and
UBSan binaries. A Clang C++11 warning-clean build is recorded when Clang is
available. The C++20 local-time build and focused probes cover the two
local-time mechanisms. Return code 77 or 127 counts as platform-gated only when
every failing command for that mechanism has an explicitly platform-gated
code; an ordinary C++20 compile failure remains a mechanism failure.

| Named verifier | Structural and executable binding |
| --- | --- |
| `fmt-duration-cast-helper` | scoped helper definitions plus integral, floating, and mixed instantiations |
| `same-arithmetic-dispatch` | both operands in the arithmetic-category trait plus compile-time matrix |
| `safe-cast-placement` | balanced directives, `detail` scope, dependency-before-use, and compiled use |
| `to-time-t-helper` | scoped template body plus large positive and negative epoch conversion |
| `templated-gmtime` | generic duration signature plus multiple representation/period calls |
| `localtime-to-time-t` | direct checked conversion plus C++20 local-time execution |
| `fractional-seconds-casts` | both scoped call sites plus positive, negative, and fractional behavior |
| `remove-old-safe-helper` | tokenized identifier absence plus all configurations compiling |
| `milliseconds-casts` | all remainder paths plus positive and negative behavior |
| `chrono-formatter-cast` | unified formatter state conversion plus integral/floating instantiations |
| `time-point-root-fix` | no narrowing in the system calendar path plus year-3000 behavior |
| `local-time-root-fix` | direct `localtime(val)` path plus feature-enabled execution |

When the standard library cannot expose the local-time branch, the report uses
`10/10 applicable; 2 platform-gated/unverified` instead of claiming 12/12.

The structural verifier treats `chrono.h` as executable template-heavy header
code across five layers: preprocessor structure, namespace/declaration scope,
template/overload structure, call-site migration, and executable behavior.

## Checkpoint training provenance

| Field | Exact value |
| --- | --- |
| Training tasks | 260 |
| Training-data manifest SHA-256 | `afec0d05d5c1f9460ac9b2ed4e65aea69775b49639c7ae727f3660308ae1b8b8` |
| Train JSONL SHA-256 | `3472d76169e52bd0859c181d63de24a060c4c7f2d3d8a004ceb6090498f1ddc1` |
| Sequence length | 4,096 |
| Global batch size | 20 |
| Training topology | 8× NVIDIA H100 |
| Source commit | `6188070622895021d1c340ad31939e888c514396` |
| Updates per epoch | 13 |

Iterations 0 through 649 represent 650 optimizer updates and exactly 50 epochs.
At step 649, the recorded loss was `0.000027910614625928666`, gradient norm
`0.0021414729699963087`, learning rate `0.00011743214109250993`, step time
`6.9253 s`, throughput `26.7814 TFLOPS`, and effective throughput
`960.2933 tokens/GPU/s`.

## Previously matched fixed-26 context

The corresponding previously recorded aggregate suite is
`glm47-synthmem-v1-ep50-fixed26-v2-v4matched-eval4-20260804T084520Z`.
This change does not rerun or recertify that fixed-26 suite.

| Sample | Single-turn Pass@1 | Feedback Pass@1 | Feedback Pass@2 |
| ---: | ---: | ---: | ---: |
| 1 | 8/26 | 9/26 | 13/26 |
| 2 | 10/26 | 7/26 | 12/26 |
| 3 | 6/26 | 4/26 | 7/26 |
| 4 | 9/26 | 8/26 | 12/26 |
| Mean | 8.25/26 | 7/26 | 11/26 |

## 1. Download and verify the checkpoint adapter

Run on a workstation authenticated to Modal:

```bash
DEST="/tmp/synthmem-v1-epoch50"
TRAINING_RUN="glm47-synth-memorization-v1-100ep-20260731T071000Z"
CHECKPOINT_REL="checkpoints/sft_lora_r16/iter_0000649"
REMOTE_ADAPTER="${TRAINING_RUN}/${CHECKPOINT_REL}/adapter"

mkdir -p "${DEST}"

modal volume get \
  glm47-runs \
  "${REMOTE_ADAPTER}" \
  "${DEST}/adapter"

printf '%s\n' "${TRAINING_RUN}" > "${DEST}/adapter/.training-run-id"

printf '%s  %s\n' \
  "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a" \
  "${DEST}/adapter/adapter_model.bin" |
  sha256sum -c -

printf '%s  %s\n' \
  "0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e" \
  "${DEST}/adapter/adapter_config.json" |
  sha256sum -c -

tar -czf /tmp/synthmem-v1-epoch50-adapter.tgz \
  -C "${DEST}" \
  adapter
```

Do not use `iter_0001299`; that is the epoch-100 checkpoint of the v1 parent
run.

## 2. Create and upload the evaluator bundle

Run from the repository root:

```bash
tar -czf /tmp/public-pr-gcp-bundle-r5-v6.tgz \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v6.jsonl \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v6.jsonl.sha256 \
  configs/public_pr_eval/private_probes \
  docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile \
  scripts/gcp_public_pr_eval_host_setup.sh \
  scripts/gcp_public_pr_eval_run.sh \
  scripts/gcp_public_pr_synthmem_50ep_eval.py \
  scripts/public_pr_repo_eval.py \
  scripts/validate_public_pr_eval.py \
  src/glm47_posttraining/public_pr_eval

sha256sum /tmp/public-pr-gcp-bundle-r5-v6.tgz \
  > /tmp/public-pr-gcp-bundle-r5-v6.tgz.sha256

export PROJECT_ID="lifeandhalf-24122025"
export VM_NAME="glm47-synthmem-50ep-pr-eval"

export ZONE="$(
  gcloud compute instances list \
    --project="${PROJECT_ID}" \
    --filter="name=${VM_NAME}" \
    --format='value(zone.basename())' |
    head -n 1
)"

test -n "${ZONE}"

gcloud compute scp \
  /tmp/public-pr-gcp-bundle-r5-v6.tgz \
  /tmp/public-pr-gcp-bundle-r5-v6.tgz.sha256 \
  /tmp/synthmem-v1-epoch50-adapter.tgz \
  "${VM_NAME}:/tmp/" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"

gcloud compute ssh "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"
```

## 3. Stage the source and adapter on the VM

Run after connecting to the VM:

```bash
cd /tmp
sha256sum -c public-pr-gcp-bundle-r5-v6.tgz.sha256

SOURCE_DIR="/opt/glm47-public-pr/source-r5-v6"
ADAPTER_PARENT="/opt/glm47-public-pr/assets/synthmem-v1-ep50"

sudo mkdir -p "${SOURCE_DIR}" "${ADAPTER_PARENT}"
sudo chown -R "${USER}:${USER}" "${SOURCE_DIR}" "${ADAPTER_PARENT}"

tar -xzf /tmp/public-pr-gcp-bundle-r5-v6.tgz \
  -C "${SOURCE_DIR}"

tar -xzf /tmp/synthmem-v1-epoch50-adapter.tgz \
  -C "${ADAPTER_PARENT}"

cd "${SOURCE_DIR}"

(
  cd configs/public_pr_eval
  sha256sum -c public-pr-repo-eval-demo-fmtlib-v6.jsonl.sha256
)

cat "${ADAPTER_PARENT}/adapter/.training-run-id"

printf '%s  %s\n' \
  "4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a" \
  "${ADAPTER_PARENT}/adapter/adapter_model.bin" |
  sha256sum -c -

printf '%s  %s\n' \
  "0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e" \
  "${ADAPTER_PARENT}/adapter/adapter_config.json" |
  sha256sum -c -
```

## 4. Run inside tmux

Create and enter a session:

```bash
tmux new-session -s synthmem-v1-ep50-v6
```

Inside that tmux session, run:

```bash
cd /opt/glm47-public-pr/source-r5-v6

export MODEL_DIR="/opt/glm47-public-pr/assets/model/GLM-4.7-Flash"
export MODEL_MANIFEST_SHA256="ac1c2693a8d8724a6aa359eb7a6778d5dda59743b1b4c45ff92986d2d1e6cecc"
export ADAPTER_DIR="/opt/glm47-public-pr/assets/synthmem-v1-ep50/adapter"
export ADAPTER_CONFIG_SHA256="0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e"
export RESULT_DIR="/opt/glm47-public-pr/results"

export CHECKPOINT_PROFILE="synthmem-v1-ep50"
export SUITE="fmtlib-verified-mechanisms-thinking"
export DOCKERFILE="docker/public-pr-synthmem-v1-ep50-gcp/Dockerfile"
export IMAGE_NAME="glm47-public-pr-gcp:synthmem-v1-ep50-thinking-v6"
export RUN_ID="synthmem-v1-ep50-thinking-fmtlib-v6-$(date -u +%Y%m%dT%H%M%SZ)"

export GCP_PROJECT="lifeandhalf-24122025"
export GCP_ZONE="us-central1-a"
export GCP_INSTANCE="glm47-synthmem-50ep-pr-eval"
export GCP_DLVM_IMAGE="common-cu129-ubuntu-2204-nvidia-580-stage"

bash scripts/gcp_public_pr_eval_run.sh 2>&1 |
  tee "/opt/glm47-public-pr/results/${RUN_ID}.console.log"
```

Detach without stopping the evaluation with `Ctrl-b`, then `d`. Reattach with:

```bash
tmux attach-session -t synthmem-v1-ep50-v6
```

## 5. Verify the completed receipt

```bash
RUN_ROOT="/opt/glm47-public-pr/results/runs/${RUN_ID}"

jq '{
  run_id,
  checkpoint_profile,
  training_run_id,
  checkpoint_identity: {
    checkpoint_path: .checkpoint_identity.checkpoint_path,
    epoch: .checkpoint_identity.epoch,
    optimizer_iteration: .checkpoint_identity.optimizer_iteration,
    source_adapter_sha256: .checkpoint_identity.source_adapter_sha256,
    serving_adapter_sha256: .checkpoint_identity.serving_adapter_sha256
  },
  inference_request,
  suite_mode,
  result: (.suite | {pass_at_1, pass_at_2})
}' "${RUN_ROOT}/run-receipt.json"

grep -R -n -F "enable_thinking: true" \
  "${RUN_ROOT}/model-settings"
```

A valid receipt must report `checkpoint_profile: synthmem-v1-ep50`,
`optimizer_iteration: 649`, and
`inference_request.thinking_enabled: true`. Every persisted initial and repair
settings file must contain `enable_thinking: true`.
