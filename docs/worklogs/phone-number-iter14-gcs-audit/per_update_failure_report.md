# Phone Number GRPO per-update failure report

The native artifacts have no epoch or iteration field. They encode a zero-based `rollout_id` in both the PT payload and `grpo[_eval]_<id>.pt` filename (0–19). Checkpoints are separate and saved at iterations 4, 9, 14, and 19.

The eval rows here are the 8-task Phone Number training monitor, not the four Fixed26 runs.

## Train

Scope: 8 Phone Number shadow-training tasks. Overall 2885/5120 passed (56.3%); first-five to last-five pass-rate delta +5.312 pp.

| Update | Pass | Fail | Pass rate | Failed compile | Failed format invalid | Failed timeout | Failed infra | Failed truncated | Dominant failed native reason | Dominant failed task | Dominant signature | Dominant failed kernel |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 0 | 126 | 130 | 49.2% | 12 | 6 | 0 | 0 | 1 | `kernel_tests_failed` (130) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (119) |
| 1 | 128 | 128 | 50.0% | 7 | 10 | 0 | 0 | 2 | `kernel_tests_failed` (128) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (30) | `observed-member-function-name-collision` (30) | `PH-E03-C` (117) |
| 2 | 134 | 122 | 52.3% | 8 | 8 | 0 | 0 | 3 | `kernel_tests_failed` (122) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (32) | `observed-member-function-name-collision` (32) | `PH-E03-C` (108) |
| 3 | 141 | 115 | 55.1% | 10 | 5 | 0 | 0 | 2 | `kernel_tests_failed` (115) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (109) |
| 4 | 140 | 116 | 54.7% | 8 | 6 | 0 | 0 | 3 | `kernel_tests_failed` (116) | `aider-shadow-cpp/phone-number--missing-definitions-repair` (30) | `declared-members-not-defined` (30) | `PH-E03-C` (110) |
| 5 | 152 | 104 | 59.4% | 7 | 6 | 0 | 0 | 1 | `kernel_tests_failed` (104) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (30) | `observed-member-function-name-collision` (30) | `PH-E03-C` (94) |
| 6 | 134 | 122 | 52.3% | 8 | 9 | 0 | 0 | 3 | `kernel_tests_failed` (122) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (116) |
| 7 | 141 | 115 | 55.1% | 8 | 9 | 0 | 0 | 2 | `kernel_tests_failed` (115) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (30) | `observed-member-function-name-collision` (30) | `PH-E03-C` (104) |
| 8 | 149 | 107 | 58.2% | 4 | 6 | 0 | 0 | 2 | `kernel_tests_failed` (107) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (96) |
| 9 | 157 | 99 | 61.3% | 2 | 2 | 0 | 0 | 1 | `kernel_tests_failed` (99) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (27) | `observed-member-function-name-collision` (27) | `PH-E03-C` (85) |
| 10 | 144 | 112 | 56.2% | 6 | 6 | 0 | 0 | 2 | `kernel_tests_failed` (112) | `aider-shadow-cpp/phone-number--missing-definitions-repair` (30) | `declared-members-not-defined` (30) | `PH-E03-C` (103) |
| 11 | 142 | 114 | 55.5% | 8 | 3 | 0 | 0 | 1 | `kernel_tests_failed` (114) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (109) |
| 12 | 153 | 103 | 59.8% | 9 | 7 | 0 | 0 | 4 | `kernel_tests_failed` (103) | `aider-shadow-cpp/phone-number--missing-definitions-repair` (30) | `declared-members-not-defined` (30) | `PH-E03-C` (97) |
| 13 | 156 | 100 | 60.9% | 7 | 5 | 0 | 0 | 2 | `kernel_tests_failed` (100) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (29) | `observed-member-function-name-collision` (29) | `PH-E03-C` (96) |
| 14 | 151 | 105 | 59.0% | 9 | 6 | 0 | 0 | 2 | `kernel_tests_failed` (105) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (31) | `observed-member-function-name-collision` (31) | `PH-E03-C` (102) |
| 15 | 148 | 108 | 57.8% | 4 | 7 | 0 | 0 | 5 | `kernel_tests_failed` (108) | `aider-shadow-cpp/phone-number--missing-definitions-repair` (29) | `declared-members-not-defined` (29) | `PH-E03-C` (99) |
| 16 | 147 | 109 | 57.4% | 4 | 8 | 0 | 0 | 5 | `kernel_tests_failed` (109) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (29) | `observed-member-function-name-collision` (29) | `PH-E03-C` (99) |
| 17 | 147 | 109 | 57.4% | 1 | 11 | 0 | 0 | 9 | `kernel_tests_failed` (109) | `aider-shadow-cpp/phone-number--missing-definitions-repair` (29) | `declared-members-not-defined` (29) | `PH-E03-C` (101) |
| 18 | 151 | 105 | 59.0% | 6 | 8 | 0 | 0 | 5 | `kernel_tests_failed` (105) | `aider-shadow-cpp/phone-number--full-solve` (27) | `missing-public-api` (27) | `PH-E03-C` (98) |
| 19 | 144 | 112 | 56.2% | 2 | 12 | 0 | 0 | 7 | `kernel_tests_failed` (112) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (29) | `observed-member-function-name-collision` (29) | `PH-E03-C` (105) |

Best update(s): [9] at 61.3%; worst: [0] at 49.2%.

Native reason totals: `kernel_tests_failed`=2235, `passed`=2885.

Native failed-reason totals: `kernel_tests_failed`=2235.

Dominant failed tasks: `aider-shadow-cpp/phone-number--eval-feedback-repair`=594, `aider-shadow-cpp/phone-number--missing-definitions-repair`=558, `aider-shadow-cpp/phone-number--full-solve`=498, `aider-shadow-cpp/phone-number--character-validation-repair`=212, `aider-shadow-cpp/phone-number--country-code-repair`=191.

Dominant failure signatures: `observed-member-function-name-collision`=594, `declared-members-not-defined`=558, `missing-public-api`=498, `letters-and-forbidden-punctuation-ignored`=212, `any-eleven-digit-country-code-accepted`=191.

Dominant failed kernels: `PH-E03-C`=2067, `PH-E04-C`=737, `PH-E02-C`=545, `PH-E02-A`=468, `PH-E03-A`=468, `PH-E04-B`=468, `PH-E01-C`=467, `PH-E02-B`=448.

## Eval

Scope: 8-task Phone Number training monitor (not Fixed26). Overall 92/160 passed (57.5%); first-five to last-five pass-rate delta +10.000 pp.

| Update | Pass | Fail | Pass rate | Failed compile | Failed format invalid | Failed timeout | Failed infra | Failed truncated | Dominant failed native reason | Dominant failed task | Dominant signature | Dominant failed kernel |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 0 | 2 | 6 | 25.0% | 2 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (6) | `aider-shadow-cpp/phone-number--character-validation-repair` (1) | `letters-and-forbidden-punctuation-ignored` (1) | `PH-E03-C` (6) |
| 1 | 4 | 4 | 50.0% | 0 | 1 | 0 | 0 | 0 | `kernel_tests_failed` (4) | `aider-shadow-cpp/phone-number--character-validation-repair` (1) | `letters-and-forbidden-punctuation-ignored` (1) | `PH-E03-C` (4) |
| 2 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 3 | 3 | 5 | 37.5% | 2 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (5) | `aider-shadow-cpp/phone-number--character-validation-repair` (1) | `letters-and-forbidden-punctuation-ignored` (1) | `PH-E03-C` (5) |
| 4 | 5 | 3 | 62.5% | 0 | 1 | 0 | 0 | 1 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 5 | 6 | 2 | 75.0% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (2) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (2) |
| 6 | 4 | 4 | 50.0% | 1 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (4) | `aider-shadow-cpp/phone-number--country-code-repair` (1) | `any-eleven-digit-country-code-accepted` (1) | `PH-E03-C` (4) |
| 7 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (2) |
| 8 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 9 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 10 | 3 | 5 | 37.5% | 1 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (5) | `aider-shadow-cpp/phone-number--character-validation-repair` (1) | `letters-and-forbidden-punctuation-ignored` (1) | `PH-E03-C` (5) |
| 11 | 6 | 2 | 75.0% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (2) | `aider-shadow-cpp/phone-number--country-code-repair` (1) | `any-eleven-digit-country-code-accepted` (1) | `PH-E03-C` (2) |
| 12 | 5 | 3 | 62.5% | 1 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 13 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 14 | 6 | 2 | 75.0% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (2) | `aider-shadow-cpp/phone-number--full-solve` (1) | `missing-public-api` (1) | `PH-E03-C` (2) |
| 15 | 4 | 4 | 50.0% | 1 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (4) | `aider-shadow-cpp/phone-number--character-validation-repair` (1) | `letters-and-forbidden-punctuation-ignored` (1) | `PH-E03-C` (4) |
| 16 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 17 | 5 | 3 | 62.5% | 1 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--country-code-repair` (1) | `any-eleven-digit-country-code-accepted` (1) | `PH-E03-C` (3) |
| 18 | 5 | 3 | 62.5% | 0 | 0 | 0 | 0 | 0 | `kernel_tests_failed` (3) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (3) |
| 19 | 4 | 4 | 50.0% | 0 | 1 | 0 | 0 | 0 | `kernel_tests_failed` (4) | `aider-shadow-cpp/phone-number--eval-feedback-repair` (1) | `observed-member-function-name-collision` (1) | `PH-E03-C` (4) |

Best update(s): [5, 11, 14] at 75.0%; worst: [0] at 25.0%.

Native reason totals: `kernel_tests_failed`=68, `passed`=92.

Native failed-reason totals: `kernel_tests_failed`=68.

Dominant failed tasks: `aider-shadow-cpp/phone-number--missing-definitions-repair`=20, `aider-shadow-cpp/phone-number--eval-feedback-repair`=18, `aider-shadow-cpp/phone-number--full-solve`=15, `aider-shadow-cpp/phone-number--character-validation-repair`=5, `aider-shadow-cpp/phone-number--country-code-repair`=4.

Dominant failure signatures: `declared-members-not-defined`=20, `observed-member-function-name-collision`=18, `missing-public-api`=15, `letters-and-forbidden-punctuation-ignored`=5, `any-eleven-digit-country-code-accepted`=4.

Dominant failed kernels: `PH-E03-C`=67, `PH-E04-C`=26, `PH-E02-C`=22, `PH-E02-B`=15, `PH-E01-A`=14, `PH-E01-C`=14, `PH-E02-A`=14, `PH-E03-A`=14.

## Critical anomalies

- `train` `compile_error`: 130 rows.
- `train` `format_invalid`: 140 rows.
- `train` `generation_truncated`: 62 rows. Native sample_status=truncated; no explicit context_exhaustion field exists.
- `train` `passed_with_format_valid_false`: 33 rows. These rows have all_tests_pass=true despite format_valid=false; treat as a verifier-field inconsistency/partial-reward nuance, not failed outputs.
- `train` `passed_with_truncated_status`: 1 rows. Excluded from the failed-truncation count because all_tests_pass=true.
- `eval` `compile_error`: 9 rows.
- `eval` `format_invalid`: 3 rows.
- `eval` `generation_truncated`: 1 rows. Native sample_status=truncated; no explicit context_exhaustion field exists.
- `eval` `passed_with_format_valid_false`: 1 rows. These rows have all_tests_pass=true despite format_valid=false; treat as a verifier-field inconsistency/partial-reward nuance, not failed outputs.
