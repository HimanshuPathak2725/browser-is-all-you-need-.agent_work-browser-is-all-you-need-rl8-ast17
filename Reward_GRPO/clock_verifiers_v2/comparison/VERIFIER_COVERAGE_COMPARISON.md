# Clock verifier coverage comparison: original versus Version 2

Version 2 detected all 14 controlled Clock faults; the original verifier set detected 12. The measured full-suite gain is 2 faults, or 14.29 percentage points, and comes from enforcing the default argument on `clock::at` and the required namespace-scope free form of `operator!=`.

This is a deterministic targeted-mutant experiment, not an estimate over arbitrary future solutions. Two independent testing agents used the same hash-pinned manifest, GCC 13.3.0, authenticated Clock fixture, canonical positive baseline, and 14-fault denominator; all 16 candidates in each run produced valid receipts with zero `INVALID` outcomes.

## Primary evidence

| Measurement | Original verifiers | Version 2 verifiers | V2 change | Detection-set similarity |
| --- | ---: | ---: | ---: | --- |
| Full verifier-set fault coverage | 12/14 (85.71%) | 14/14 (100.00%) | +2; +14.29 pp | Jaccard 85.71%; binary agreement 85.71% |
| Shaping-policy fault coverage | 10/14 (71.43%) | 13/14 (92.86%) | +3; +21.43 pp | Jaccard 76.92%; binary agreement 78.57% |
| Official terminal fault coverage | 11/14 (78.57%) | 11/14 (78.57%) | 0; 0.00 pp | Jaccard 100.00%; binary agreement 100.00% |
| Canonical positive control | 5/5 policies PASS | 8/8 policies PASS | No regression | Both full suites accept |
| Evaluator validity | 0/16 `INVALID` | 0/16 `INVALID` | No difference | 100% valid-run agreement |

“Detected” means at least one policy returned `FAIL`; `INVALID` never counts as detection. Shaping means CL-E01/E02/E04/E05 for the original set and CL2-C01–C07 for v2. Terminal means CL-E03 and CL2-C08 respectively. Jaccard is intersection divided by union of detected faulty-sample IDs; binary agreement is equal detected/not-detected labels across all 14 faults.

## Experimental design and controls

The comparison contains 14 deterministic candidates, each produced from the same canonical `clock.h` and `clock.cpp`. The manifest records the intended fault class and both candidate file hashes. Agent A ran only the five original policies; Agent B ran only the eight v2 policies. Each agent copied the same pinned exercise fixture into its own `/tmp` tree, overlaid only the candidate files, and used new output directories for every policy or aggregate run.

The canonical baseline matches the pinned `.meta/example.h` and `.meta/example.cpp` byte-for-byte:

- `clock.h`: `74bb7ea77a1a11a856065976fbc421da450112df5e38e232b83c63e072c60c62`
- `clock.cpp`: `f269249dfeae1939942a7f3335d9f058e8e1c0de7e74205d7cb44eb1d5822269`
- comparison manifest: `7ee634c09bbafadc2670c8aa3514de0623bddc8fae382b9f788acbf2383a6821`

A pre-run quality check rejected the first F06 design: `char[6]` fit `HH:MM\0` in this implementation and was accepted by GCC. F06 was corrected to `char[5]`; direct strict compilation then produced `-Werror=format-truncation`. Both preliminary agent runs were discarded, their work directories were recreated, and every reported result comes from the corrected manifest.

## Per-sample evidence

| Sample and fault | Original failed policies | V2 failed policies | Official terminal | Full-suite verdict |
| --- | --- | --- | --- | --- |
| F01 C++20 spaceship under C++17 | E01–E05 | C01–C08 | Both FAIL | Both detect |
| F02 missing `<iomanip>` | E01–E05 | C01–C08 | Both FAIL | Both detect |
| F03 missing `operator!=` | E03 | C03, C04, C05, C07, C08 | Both FAIL | Both detect; v2 also shapes |
| F04 constructor definition not declared | E01–E05 | C01–C08 | Both FAIL | Both detect |
| F05 non-inline header `operator!=` | E01–E05 | C01–C08 | Both FAIL | Both detect |
| F06 undersized `snprintf` buffer | E01–E05 | C01–C08 | Both FAIL | Both detect |
| F07 unpadded `H:M` formatting | E02, E03, E04, E05 | C06, C07, C08 | Both FAIL | Both detect |
| F08 exact-day normalization emits `24:00` | E02, E03, E04 | C07, C08 | Both FAIL | Both detect |
| F09 `plus()` adds one extra minute | E02, E03, E04, E05 | C07, C08 | Both FAIL | Both detect |
| F10 `minus()` ignores its argument | E02, E04, E05 | C07 | Both PASS | Both detect through shaping |
| F11 equality ignores minutes | E02, E03 | C07, C08 | Both FAIL | Both detect |
| F12 corruption only at official input `(201, 3001)` | E03 | C08 | Both FAIL | Both detect through terminal only |
| F13 missing default argument on `at` | — | C02, C03, C05 | Both PASS | Original misses; v2 detects |
| F14 member `operator!=` replaces required free function | — | C03 | Both PASS | Original misses; v2 detects |

Policy failures overlap. A fatal compile defect can fail multiple downstream compile/link policies, so the table is evidence of detection and localization paths, not independent fault observations. The meaningful aggregate is the union of detected sample IDs.

## Coverage interpretation

### Directly established facts

- Version 2’s full set is a strict superset of the original set’s detections on this corpus: v2 has two exclusive detections and the original has none.
- Both terminal policies detect the exact same 11 faults. F10, F13, and F14 pass the official suite; F12 is detected only by the official suite in both packs.
- V2 shaping adds F03, F13, and F14 relative to original shaping. F03 was already caught by the original terminal policy, while F13 and F14 were complete original-suite misses.
- C03 is the decisive v2 policy for the required free `operator!=`; C03 also rejects the missing default argument, with C02 and C05 independently exposing that missing call surface.
- The original pack’s shaping policies still add real value: F10 passes CL-E03 but fails E02, E04, and E05.

### Engineering inference

For the known Clock failure taxonomy, v2 closes the demonstrated exact-API blind spots without reducing observed terminal coverage or rejecting the canonical reference. The additional shaping signals also localize the missing inequality case before terminal evaluation. This supports using v2 as the stronger strict-contract regression pack for Clock, while retaining C08 as the mandatory official terminal gate.

This does not show that eight policies are intrinsically better than five or that v2 will detect every unseen bug. The sample set was deliberately constructed from known failure categories, including the gaps v2 was designed to close, so the result is appropriate for regression validation but optimistic as a population-level coverage estimate.

## Official-perfect dataset control: contract boundary

The dataset’s `a01-clock-turn2` control passes both official terminal policies, confirming its perfect status under the pinned Exercism tests. It fails both full strict verifier packs and is excluded from the 14-fault denominator:

| Control observation | Original | Version 2 | Meaning |
| --- | --- | --- | --- |
| Official terminal | CL-E03 PASS | CL2-C08 PASS | Official behavior accepted |
| Strict shaping | E01, E02, E04, E05 FAIL | C02, C03, C05, C07 FAIL | Strict API contract rejected |
| Full suite | FAIL | FAIL | False rejection if “correct” means official tests only |

The observed API differences are concrete: the control exposes a public constructor, requires two arguments for `at`, returns new values from `const plus/minus`, and implements member `operator!=`; the canonical strict contract uses a private constructor, defaulted `at(hour, minute = 0)`, mutating reference-returning `plus/minus`, and a namespace-scope free `operator!=`. Therefore the reward contract must be chosen explicitly:

- If the target is exact canonical API shape, full v2 behavior is consistent with that objective.
- If the target is Exercism official acceptance, the full original and v2 packs both over-constrain valid alternatives; only the authenticated terminal result should determine correctness, with strict policies used as diagnostics rather than negative reward.

## Evidence, boundaries, and reproducibility

Persistent artifacts:

- [Fault manifest](manifest.json)
- [Original agent result](results/original_results.json) and [agent report](results/original_agent_report.md)
- [Version 2 agent result](results/v2_results.json) and [agent report](results/v2_agent_report.md)
- [Machine-readable coverage summary](results/coverage_summary.json)
- [Sample generator](generate_samples.py), [v2 reproduction runner](run_v2_agent.py), and [coverage analyzer](analyze_coverage.py)

Agent A produced 80 fresh policy receipts under `/tmp/clock-original-agent-a-20260822-rerun/receipts`. Agent B produced 16 aggregate and 128 policy receipts under `/tmp/clock-v2-agent-comparison-receipts` and re-hashed all 144 recorded receipts with zero mismatches. The normalized result hashes are `03edc31ae6f3d945e59978010cdef123142660c521d7f70d25a1ce4599f4f01e` for original and `5d3c691b825ca60acd7fc4493419a286e28ae5b645dfe668a4871c30cccd455f` for v2.

Unverified boundaries are other compilers, other Clock implementations, generated/random mutants, concurrency and timeout behavior under production load, and correlation between shaping rewards and RL learning quality. The `/tmp` command receipts are machine-local and ephemeral; the normalized JSON, recorded hashes, sample sources, generator, and analyzer are persistent in this repository.

## Conclusion

Version 2 is the stronger strict-contract verifier for this controlled Clock corpus: 100% versus 85.71% full-suite detection, with identical 78.57% official-terminal coverage. The concrete gain is exact-API enforcement, not broader official behavior. Before enabling full v2 failures as negative RL reward, decide whether training should reproduce the canonical API exactly or accept every implementation that passes Exercism’s official tests; the perfect dataset control proves those objectives are currently different.
