# How the R5 Prompt Uses Aider-Style Repository Editing

## Scope of this explanation

This document explains the prompt and execution contract used by GCP run:

```text
synthmem-v1-ep50-thinking-fmtlib-v5-20260807T175846Z
```

The exact evaluation row is:

```text
configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v5.jsonl
```

Its JSONL SHA-256 is:

```text
db8de1a51420ba5424f1799ea15e81adeaadaeb3dcd6331ce94412d98c223202
```

The prompt itself is digest-bound by `integrity.model_prompt_sha256`:

```text
c2e80dccbd50d0c9e1e38ba06a4c021821ac82fb16ba500ac0358a4fe5e9ced5
```

## Short answer

The run uses a real Aider repository-edit workflow. The JSONL supplies one task message, while the evaluator launches Aider against a prepared fmtlib repository with only `include/fmt/chrono.h` editable and with Aider's `diff` edit format selected. The model is required to return applicable edits rather than a prose answer. Aider applies those edits to the candidate workspace, and the evaluator derives the authoritative candidate patch from the resulting Git diff.

This run uses Aider **diff format**, not Aider whole-file replacement format. Thinking mode and best-of-four sampling are additional inference/evaluation controls; they are not the reason the prompt is Aider-style.

## Contract evidence

| Contract layer | Exact value | Why it is Aider-style |
|---|---|---|
| Message envelope | Exactly one message with `role: "user"` | Supplies a task instruction to Aider through its message-file interface rather than pretending that a normal chat response is the final artifact. |
| Response protocol | `aider_diff_workspace_edit` | Explicitly identifies the expected response as an Aider diff-based repository edit. |
| Output kind | `workspace_edit` | Success requires a repository mutation, not an explanatory final answer. |
| Edit format | `diff` | The runner passes `--edit-format diff` to Aider. This is distinct from `whole`. |
| Editable file | `include/fmt/chrono.h` | Aider is launched with this exact file as its editable repository context. |
| Scope mode | `exact_allowlist` | The model may modify the named production file and no other path. |
| Candidate source | `git_diff_against_evaluator_baseline` | The evaluator judges what Aider actually changed in the repository, not merely the text printed by the model. |
| Prose-only handling | `final_answer_text_is_not_a_substitute_for_workspace_changes: true` | A textual claim or proposed patch that does not become a workspace change is not accepted as completion. |
| Malformed output | `attempt_failure` | An unusable Aider edit response fails the attempt rather than being treated as a solution. |
| Network and repo map | Model network disabled; Aider invoked with `--map-tokens 0` | The task is solved from the explicitly supplied editable file context, without arbitrary network lookup or repository-map retrieval. |

## Prompt anatomy

The stored user message follows a repository-edit task structure that is suitable for Aider:

| Prompt section | Role in an Aider task |
|---|---|
| `# Objective` | States the production defect and the general behavior to implement. |
| `# Model and evaluator boundary` | Explains that files arrive through Aider, the model has no terminal or network, and the evaluator—not the model—runs compilation. |
| `# Failure reproduction` | Gives a small C++ reproduction and expected public behavior without granting access to evaluator-only artifacts. |
| `# Required behavior` | Defines observable requirements the repository edit must preserve or fix. |
| `# Compatibility and invariants` | Constrains the patch to C++11, public-API compatibility, thread safety, locale behavior, and safe arithmetic. |
| `# Editable scope` | Names `include/fmt/chrono.h` as the only editable path and forbids tests and unrelated files. |
| `# Validation expectations` | Separates the model's edit responsibility from the harness's build, test, and probe responsibility. |
| `# Response contract` | Requires Aider diff edits and rejects prose as a replacement for editing the repository. |
| `# Implementation map` | Gives concrete code locations, dependency ordering, helper shapes, and a finite consumer-migration ledger. |
| `# Do-not-change invariants` | Protects neighboring overloads, feature guards, namespace boundaries, and preprocessor structure from overly broad edit blocks. |
| `# Final patch audit` | Gives ten task-specific checks for the model to perform on its proposed edit before returning it. |

This structure is important for Aider because an edit model needs both the desired behavior and precise repository boundaries. The prompt therefore describes where the code belongs, what existing structure must remain intact, and what counts as a valid workspace change.

## How the JSONL becomes an Aider model request

The execution flow is:

```text
JSONL model_input.messages[0].content
        |
        v
attempt-1-message.txt
        |
        v
Aider CLI with --message-file and --edit-format diff
        |
        +--> editable repository file: include/fmt/chrono.h
        |
        v
model emits Aider diff edits
        |
        v
Aider applies edits to an isolated repository copy
        |
        v
evaluator derives Git diff, enforces scope, builds, tests, and scores
```

The runner constructs the equivalent of this command for each isolated candidate:

```bash
python -m aider \
  --model openai/glm47-synthmem-v1-ep50-public-pr \
  --edit-format diff \
  --model-settings-file PRIMARY_SETTINGS_FILE \
  --message-file attempt-1-message.txt \
  --chat-history-file chat-history.md \
  --yes-always \
  --no-auto-commits \
  --no-dirty-commits \
  --no-gitignore \
  --no-check-update \
  --no-stream \
  --map-tokens 0 \
  --no-auto-lint \
  --no-auto-test \
  include/fmt/chrono.h
```

`PRIMARY_SETTINGS_FILE` is a placeholder above because its concrete location is runtime-specific. The flags and editable file are the relevant stable contract. Aider adds its own edit-format instructions and the current editable file contents around the task message at inference time. Therefore, the JSONL does not need to duplicate the full file or hardcode Aider's complete runtime wrapper.

In conceptual terms, Aider's diff mode asks for narrowly matched search-and-replace edit blocks of this shape:

````text
include/fmt/chrono.h
```cpp
<<<<<<< SEARCH
exact existing code
=======
replacement code
>>>>>>> REPLACE
```
````

The exact wrapper is owned by the installed Aider version. The evaluation contract freezes the mode through `--edit-format diff`; the task prompt reinforces that the returned blocks must be narrow and applicable to the current file text.

## Why the prompt is not merely asking for a patch in prose

Several independent controls make this a workspace-edit evaluation:

1. The prompt says to return applicable Aider diff edits and not prose.
2. The JSONL declares `kind: workspace_edit` and `edit_format: diff`.
3. The runner invokes Aider with the editable file path.
4. Aider applies accepted edits inside an isolated repository copy.
5. The harness calculates the candidate patch from Git state against the evaluator baseline.
6. A nonempty production change to `include/fmt/chrono.h` is mandatory.
7. Changes to any other path trigger the hard scope gate.
8. A final text answer cannot substitute for an applied repository edit.

That combination prevents a model from receiving credit merely for describing the correct fix.

## Attempt-two repair remains Aider-style

Each candidate has at most two turns. When attempt one fails compilation, the evaluator may create `attempt-2-message.txt` containing only the first sanitized compiler diagnostic rooted in the editable header. It then invokes Aider again with:

```text
--restore-chat-history
```

The second turn therefore repairs the existing Aider workspace and conversation rather than starting an unrelated chat answer. It uses repair temperature `0.2`; the initial turn uses temperature `0.7`. Private test output is not disclosed.

## Thinking mode is separate from edit format

The run enabled GLM thinking through:

```text
chat_template_kwargs.enable_thinking=true
```

This controls model reasoning behavior at the OpenAI-compatible chat transport. It does not change the required output type. After reasoning, the response still has to conform to Aider's diff-edit protocol and produce an applied workspace change.

Similarly, four seeds (`1701` through `1704`) create four isolated Aider candidates. Best-of-four selection changes sampling and selection, not the prompt's repository-edit format.

## Privacy and evaluation boundary

The outer JSONL row contains evaluation provenance, scoring rules, and evaluator-only validation metadata. Those outer fields are not all copied into `model_input.messages[0].content`.

In particular:

- the model-facing prompt describes public behavior and the editable production file;
- the upstream PR URL and reference commit remain provenance fields outside the model message;
- the reference patch remains evaluator-only;
- private validation implementation and private test output are not supplied to the model; and
- this public-PR-derived task is marked `training_eligibility: forbidden` and is evaluation-only.

This boundary is consistent with the repository's Aider scope policy: held-out evaluation prompts, references, tests, and response histories must not become positive training data.

## What the R5 failure proves about format handling

The R5 candidates produced real changes to `include/fmt/chrono.h`, and the evaluator advanced those workspaces to the `build-chrono` stage. Candidate 03 reached 7/12 partial-inclusive diagnostic coverage before failing compilation; candidate 01 was evaluator-selected and also failed compilation.

Therefore, the observed terminal issue was not a missing workspace edit or an Aider response-envelope failure. The Aider workflow applied candidate code successfully enough for the compiler to inspect it. The terminal issue was C++ correctness:

- candidate 03 passed a duration to a helper accepting a `system_clock::time_point`; and
- candidate 01 omitted a template declaration and introduced helper scope/visibility errors.

The official executable result remains 0/1. See `error-report.md` in this directory for the complete run and compiler-error analysis.

## Exact conclusion

The prompt follows Aider style at both required levels:

- **Instruction level:** it asks for a scoped, applicable repository edit with explicit file, behavior, compatibility, and edit-block constraints.
- **Execution level:** the evaluator actually runs Aider with `--edit-format diff`, supplies `include/fmt/chrono.h` as the editable file, applies the response in an isolated workspace, and scores the resulting Git diff.

It should be described as an **Aider diff workspace-edit prompt with one sanitized compiler-repair turn**, not as a plain chat prompt, an Aider whole-file prompt, or an SFT training row.
