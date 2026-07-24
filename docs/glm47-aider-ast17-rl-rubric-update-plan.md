# GLM-4.7 Aider AST17 RL Rubric Update Plan

This note records the current Aider Polyglot C++ GRPO reward/rubric behavior
and the updates needed after the completed run
`glm47-aider-ast17-grpo-main-20260724-035206`.

The run completed successfully, but the reward and monitor eval curves showed
only a small noisy lift, while passrate stayed at `0.0`. The likely issue is
not that the shadow data is unusable; it is that the current RL reward is too
bucketed and gives too little ranking signal before a completion already
compiles or passes hidden tests.

## Evidence From Completed GRPO Run

| Field | Value |
| --- | --- |
| GRPO run ID | `glm47-aider-ast17-grpo-main-20260724-035206` |
| Final checkpoint | `iter_0000025` |
| Training status | `success` |
| Training gate | `passed` |
| RL train split | `data/grpo/train.jsonl` |
| RL train task count | `253` |
| RL monitor split | `data/eval/train_monitor.jsonl` |
| RL monitor task count | `32` |
| Initial monitor eval reward | about `-0.55625`, then `-0.546875` at logged eval 0 |
| Best monitor eval reward | `-0.509375` at eval 15 and eval 22 |
| Final monitor eval reward | `-0.537500` at eval 25 |
| Final training-loop pass@1/pass@2/pass@4/pass@8 | `0.0 / 0.0 / 0.0 / 0.0` |

Training completed cleanly, but the reward trend was not strong enough to
produce a visible passrate lift.

## Current Rubric And Reward Shape

| Area | Current behavior | Code reference | Issue |
| --- | --- | --- | --- |
| Fatal parse failure | Returns `-0.8` for invalid/no-file output. | `src/glm47_posttraining/aider_polyglot/reward.py::compute_production_aider_reward` | Clarification answers, no-file answers, wrong format, and other fatal parse failures collapse into one bucket. |
| Forbidden file/runtime primitive | Returns `-1.0`. | `src/glm47_posttraining/aider_polyglot/reward.py` | This is appropriate and should remain a hard floor. |
| Compile failure | Returns `-0.5`. | `src/glm47_posttraining/aider_polyglot/reward.py` | All compile failures get the same reward, so GRPO cannot rank a near-fix above broken code. |
| Candidate timeout | Returns `-0.5`. | `src/glm47_posttraining/aider_polyglot/reward.py` | Reasonable as a hard negative, but timeout type should be separately tracked. |
| Sanitizer failure | Returns `-0.5`. | `src/glm47_posttraining/aider_polyglot/reward.py` | Reasonable as a hard negative, but should remain separate telemetry. |
| Partial tests | Returns `0.6 * tests_passed / tests_total`. | `src/glm47_posttraining/aider_polyglot/reward.py` | Good when available, but only useful when the hidden grader exposes ordered partial checks. |
| AST17/style | Computed only after all tests pass. | `src/glm47_posttraining/aider_polyglot/reward.py` | Almost no samples reach this, so it gives almost no training signal. |
| Full pass | `0.80*S_Aider + 0.10*S_AST17 + 0.10*S_style - bloat`, clamped to `[0, 1]`. | `src/glm47_posttraining/aider_polyglot/reward.py` | Correctness should dominate more strongly; full pass should have a reward floor. |
| Style score | `s_style = s_ast17`. | `src/glm47_posttraining/aider_polyglot/reward.py` | Style is currently duplicate telemetry, not an independent signal. |
| Parser | Requires whole-file Aider format with editable file labels. | `src/glm47_posttraining/aider_polyglot/parser.py` | Safe, but parse failures need more detailed categories for RL. |
| Signal gate | Optional via `GLM47_AIDER_REQUIRE_SIGNAL`. | `src/glm47_posttraining/integrations/miles_aider_polyglot.py` | The full run did not require strong first-rollout reward variance by default. |

## Main Diagnosis

The current setup is pass@1-aligned, but it is too sparse for GRPO at this
stage. Most completions land in broad buckets such as fatal parse failure or
compile failure. Because GRPO learns from relative reward differences inside
each prompt group, flat buckets produce weak advantages even when some samples
are qualitatively better.

The biggest missing signal is not more final hidden-test strictness. The
biggest missing signal is useful ranking among non-passing completions:

- A response with no files should be worse than a response with recoverable
  labels.
- A response that compiles but fails tests should be better than one with a
  syntax error.
- A response that passes early invariant checks should be better than one that
  fails the first check.
- A response using the requested mechanism should receive a small bonus even
  before it passes every hidden test.

## Prioritized Updates

| Priority | Update | Expected effect |
| --- | --- | --- |
| P0 | Add detailed parse/format reward buckets: `clarification_only`, `no_files`, `wrong_label`, `recoverable_label`, `exact_format`. | Makes bad-format samples rankable instead of all receiving the same fatal parse reward. |
| P0 | Add compile diagnostic shaping for syntax errors, missing includes/types, linker/API mismatch, warning-as-error, and template/type errors. | Lets GRPO prefer near-compiling code over completely broken code. |
| P0 | Compute a lightweight pre-pass AST/mechanism score after parsing, not only after full pass. Cap this to a small range such as `0.03` to `0.07`. | Provides dense structure signal before hidden tests pass. |
| P0 | Add a full-pass reward floor, for example `reward >= 0.85` whenever all hidden tests pass. | Guarantees any correct solution outranks partial or stylistically good failures. |
| P1 | Ensure every shadow grader exposes ordinal partial checks where feasible. | Makes `tests_passed/tests_total` meaningful across most tasks. |
| P1 | Enable the first-rollout signal gate by default for full GRPO runs. | Stops weak-signal runs early instead of spending hours on flat rewards. |
| P1 | Add explicit `clarification_without_files` detection. | The prompt permits asking questions, but benchmark success requires file output; this failure should be tracked separately. |
| P1 | Add per-rollout reason-count telemetry to the artifacts and W&B. | Makes it easy to see whether training is blocked by parse, compile, timeout, partial-test, or reward-collapse issues. |
| P2 | Replace `s_style = s_ast17` with a real independent style score. | Avoids duplicate AST telemetry and gives clearer style reward accounting. |
| P2 | Add task-family/category reward summaries. | Identifies whether specific task families are too hard or too flat for RL. |

## Proposed Reward Shape

The reward should remain pass@1-aligned, but it needs more levels before full
success:

| Outcome | Proposed reward |
| --- | ---: |
| Forbidden file or verifier bypass | `-1.00` |
| Clarification-only answer with no file output | `-0.90` |
| Fatal no-file parse failure | `-0.80` |
| Recoverable format issue with editable code extracted | `-0.65` to `-0.45` |
| Compile failure | `-0.55` to `-0.30`, based on diagnostic class |
| Runs but passes zero tests | `0.05` to `0.12` |
| Partial tests pass | `0.10 + 0.70 * fraction_passed + small format/mechanism bonus` |
| Full pass | `max(0.85, 0.90 + small AST/style bonus - capped bloat)` |

The exact constants should be validated on a saved rollout dump before a full
training rerun. The important invariant is:

```text
forbidden < fatal parse < recoverable format < compile failure with useful code
  < runtime zero-pass < partial pass < full pass
```

## Implementation Notes

### Parse And Format Buckets

Update `parse_whole_file_response` or wrap its exceptions to distinguish:

- no fenced block
- fenced block without editable file label
- response asks a clarifying question and includes no files
- path-prefixed but basename-recoverable label
- wrong non-editable target
- duplicate file
- unsupported fence language

Do not relax protected file rejection. Non-editable files, test files, CMake
files, absolute paths, or parent-directory paths must remain hard failures.

### Compile Diagnostic Buckets

Use harness compile logs to classify common failure modes:

- missing include
- unknown type/name
- signature/API mismatch
- missing required function/class
- linker error
- warning-as-error
- syntax parse error

These should still be negative, but not identical. A candidate that writes both
expected files and only has a small missing include should rank above a
candidate that outputs malformed or unrelated code.

### Pre-Pass AST/Mechanism Signal

Run the lightweight AST/mechanism score for parsed candidates even when the
hidden tests fail or compilation fails, as long as source extraction is safe.
Keep the bonus small so hidden-test correctness remains dominant.

Candidate examples:

- uses required public API names
- includes both required files when two files are editable
- avoids forbidden raw allocation/runtime primitives
- has plausible C++17 structure
- mentions or implements capability terms from the task prompt

### Full-Pass Floor

The current full-pass formula can reduce a correct answer due to style and
bloat. Correctness should be a hard separator. Any all-tests-pass result should
receive at least `0.85`, and normal clean full passes should land near `0.90`
to `1.00`.

### Signal Gate

Set full GRPO runs to require a useful first rollout:

```text
GLM47_AIDER_REQUIRE_SIGNAL=1
GLM47_AIDER_MIN_REWARD_VARIANCE_GROUPS=4
GLM47_AIDER_MIN_SEMANTIC_VARIANCE_GROUPS=2
GLM47_AIDER_MIN_EXACT_FORMAT_RATE=0.75
GLM47_AIDER_MIN_COMPILE_RATE=0.90
```

If the first rollout cannot satisfy those thresholds, rerun with a fixed reward
or sampling setup instead of continuing a weak-signal training run.

## Validation Plan

1. Re-score a saved rollout dump with the old reward and the new reward.
2. Compare reason distributions and within-group reward variance.
3. Confirm full passes always outrank partial passes.
4. Confirm forbidden/protected-file outputs remain hard failures.
5. Confirm compile failures are still negative but no longer flat.
6. Run a one-update GRPO profile and inspect the signal-gate receipt.
7. Only then run the full 26-update GRPO training.

## Expected Outcome

These changes should not make the benchmark easier in the final fixed-26 eval.
They should make training less sparse by giving GRPO useful gradients before a
sample reaches full correctness. The desired result is not inflated reward; the
desired result is better within-group ranking so the policy can move toward
compiling, test-passing Aider whole-file responses.
