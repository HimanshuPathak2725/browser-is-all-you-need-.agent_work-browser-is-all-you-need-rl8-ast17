# Policy 5: Empty and small-input safety

This diagnostic policy isolates the directly observed empty-input `SIGFPE` and `SIGSEGV` failures without prescribing an implementation. It calls only the exact public API and runs each group in a separate verifier process.

| Kernel | Binary pass condition | Evidence |
|---|---|---|
| 5A | Every observer returns the expected empty result for empty and punctuation-only inputs without crashing. | Isolated compile/run receipt |
| 5B | Singleton and one-row inputs return the expected normalized, size, segment, compact, and formatted results. | Isolated compile/run receipt |
| 5C | A bounded small-domain sweep preserves normalization, dimensions, segments, and output-size invariants. | Isolated compile/run receipt |

## Failure-gap audit

The motivating failures are `crypto-square-kernel12-grpo20-rerun-20260821T173527Z/grpo_00/sample_000` (`SIGSEGV`) and `.../grpo_00/sample_040` (`SIGFPE`). Both fail the authenticated official suite. The unchanged v2 verifier process died before emitting a receipt; E05 localizes those candidate faults as `[-1,+1,-1]` and `[-1,-1,-1]` instead of erasing every unrelated signal.

The 49-case replay also found five official-passing candidates that E05 rejects because their public helper behavior differs from the diagnostic oracle. Those exact source IDs are recorded in `validation/failure_gap_manifest.json`. E05 is therefore not a default terminal gate: an authenticated official pass overrides E05, and E05 contributes shaped diagnostics only while official behavior is failing.

## Controls and INVALID

The canonical reference and a private-field-only rename must return `[+1,+1,+1]`. The empty-input crash mutation must fail 5A and 5C while preserving 5B. A changed protected asset, wrong GCC identity, missing compiler, source mutation during execution, or unusable receipt is `INVALID`, never candidate `-1`.

## Aggregation

The diagnostic sum ranges from `-3` to `+3`. Full E05 success requires all three kernels, but default task success is determined only by authenticated Policy 3.

## Run

    python3 verifiers/verifier_05_empty_small_input_safety.py --exercise-dir TASK --output-dir NEW_EMPTY_DIR
