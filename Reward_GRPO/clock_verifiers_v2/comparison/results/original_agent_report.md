# Agent A: Original Clock Verifier Results

Agent A independently evaluated the canonical baseline, the dataset-derived official-pass control, and all 14 declared faulty samples with only the five original Clock policies. Every candidate hash matched manifest SHA-256 `7ee634c09bbafadc2670c8aa3514de0623bddc8fae382b9f788acbf2383a6821`; every policy ran against a fresh output directory using GCC 13.3.0 and the authenticated pinned fixture.

The original verifier set detected 12 of 14 faults (85.71%) with zero INVALID outcomes. CL-E03 detected 11 faults, while the four shaping policies collectively detected 10; their union added one real gain over the official suite by detecting `f10_minus_noop`, but missed `f13_missing_default_argument` and `f14_member_instead_of_free_inequality`.

| Candidate | Declared fault/control | CL-E03 terminal | Shaping union | Original suite |
|---|---|---:|---:|---:|
| `canonical_baseline` | Positive baseline | PASS | PASS | PASS |
| `dataset_official_pass` | Non-denominator control | PASS | FAIL | FAIL |
| `f01_cxx20_spaceship` | Language mode | FAIL | FAIL | FAIL |
| `f02_missing_iomanip` | Dependency | FAIL | FAIL | FAIL |
| `f03_missing_inequality` | Exact API | FAIL | PASS | FAIL |
| `f04_missing_constructor_declaration` | Header/source | FAIL | FAIL | FAIL |
| `f05_noninline_header_operator` | ODR/linkage | FAIL | FAIL | FAIL |
| `f06_snprintf_warning` | Warning cleanliness | FAIL | FAIL | FAIL |
| `f07_unpadded_format` | Formatting | FAIL | FAIL | FAIL |
| `f08_negative_whole_day` | Normalization | FAIL | FAIL | FAIL |
| `f09_plus_off_by_one` | Arithmetic | FAIL | FAIL | FAIL |
| `f10_minus_noop` | Arithmetic API | PASS | FAIL | FAIL |
| `f11_equality_ignores_minutes` | Equality | FAIL | FAIL | FAIL |
| `f12_official_rare_case` | Official-only case | FAIL | PASS | FAIL |
| `f13_missing_default_argument` | Exact API default | PASS | PASS | PASS |
| `f14_member_instead_of_free_inequality` | Exact API operator form | PASS | PASS | PASS |

## Policy coverage

| Policy | Faults rejected | Directly observed role |
|---|---:|---|
| CL-E01 | 5/14 | Public API compile, signature, and implementation link probes |
| CL-E02 | 10/14 | Independent semantic boundary groups |
| CL-E03 | 11/14 | Authenticated official build and test execution |
| CL-E04 | 9/14 | Canonical construction and arithmetic groups |
| CL-E05 | 8/14 | Factory, observer, signature, and linkage groups |
| Any original policy | 12/14 | Union of all five policies |

## Controls and interpretation

- The canonical pinned reference passed all 15 kernels across the five policies. This is direct evidence that the verifier pack and fixture were operational for this run.
- The dataset control passed CL-E03 but failed CL-E01, CL-E02, CL-E04, and CL-E05 because its API shape differs from the stricter pinned contract. It is excluded from the faulty-sample denominator, so this does not inflate fault coverage.
- `f03_missing_inequality` and `f12_official_rare_case` were detected only by CL-E03. Conversely, `f10_minus_noop` passed CL-E03 and was detected only by shaping policies, demonstrating complementary coverage.
- `f13_missing_default_argument` and `f14_member_instead_of_free_inequality` passed every original policy. These are confirmed misses for the declared strict-contract faults in this controlled sample set.
- Coverage is measured only over these 14 targeted mutants. It does not establish a general population error-detection rate.

## Audit artifacts

- Normalized result: `Reward_GRPO/clock_verifiers_v2/comparison/results/original_results.json`
- Complete policy receipts: `/tmp/clock-original-agent-a-20260822-rerun/receipts`
- Isolated candidate fixtures: `/tmp/clock-original-agent-a-20260822-rerun/fixtures`
- Pinned fixture source: `/tmp/clock-verifier-audit.AjXhUg/practice/clock`
- Compiler: `g++` 13.3.0
- INVALID candidates: 0/16

The original verifier set is operational and materially stronger than the official terminal check alone, but it does not enforce the default argument on `clock::at` or the required free-function form of `operator!=`.
