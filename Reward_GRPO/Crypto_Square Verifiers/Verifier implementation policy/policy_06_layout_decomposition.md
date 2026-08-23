# Policy 6: Layout decomposition

This diagnostic policy decomposes correct transposition, separator geometry, and trailing padding without adding any verifier material to model context.

| Kernel | Binary pass condition | Evidence |
|---|---|---|
| 6A | Compact ciphertext transposes columns correctly on perfect, incomplete, and long rectangles. | Isolated compile/run receipt |
| 6B | Normalized ciphertext has exactly `c` chunks of `r` characters with separators at the required boundaries. | Isolated compile/run receipt |
| 6C | Compact content and normalized trailing padding match an independent oracle on varied incomplete rectangles. | Isolated compile/run receipt |

## Failure-gap audit

The dominant real failure is `crypto-square-kernel12-grpo20-rerun-20260821T173527Z/grpo_00/sample_009`. The unchanged v2 vector `110110110110` and authenticated official failure already rejected it, so E06 does not close a missed terminal failure. E06 adds localization: the candidate returns `[+1,-1,-1]`, separating preserved compact transposition from broken grouping and padding.

Two official-passing controls—`.../grpo_05/sample_1434` and `.../grpo_06/sample_1559`—fail E06 helper/extended-input checks. E06 is therefore diagnostic-only in default reward. An authenticated official pass must receive full terminal credit regardless of E06; strict helper conformance may be reported separately but cannot narrow default success.

## Controls and INVALID

The canonical reference and private-field-only rename must return `[+1,+1,+1]`. The unspaced-layout mutation must return `[+1,-1,-1]`. A changed protected asset, wrong GCC identity, missing compiler, source mutation during execution, or unusable receipt is `INVALID`.

## Aggregation

The diagnostic sum ranges from `-3` to `+3`. Full E06 success requires all three kernels, while authenticated Policy 3 alone decides default task success.

## Run

    python3 verifiers/verifier_06_layout_decomposition.py --exercise-dir TASK --output-dir NEW_EMPTY_DIR
