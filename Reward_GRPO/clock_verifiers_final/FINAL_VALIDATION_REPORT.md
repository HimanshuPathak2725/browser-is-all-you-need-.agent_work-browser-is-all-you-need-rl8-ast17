# Final unified Clock verifier: design and validation report

The final package consolidates the strongest original and Version 2 logic into six policies: build integrity, exact API, multi-translation-unit integration, exhaustive formatting, property-based time semantics, and the authenticated official terminal suite. The runner executes all six against one source snapshot, records individual receipts, verifies cross-policy source consistency, and exposes official and strict acceptance decisions separately.

The final clean campaign passed: the canonical reference passed 18/18 kernels, all 23 controlled faults were rejected in strict mode, the original 14-fault corpus remained 14/14 detected, the withheld official-only mutant failed only C06, and both evaluator-fault controls produced `INVALID` in all six policies. This is strong regression evidence for the tested taxonomy, not proof against every possible implementation or adversarial program.

## Primary evidence

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| CLF-C01 build integrity | Language mode, missing dependencies, declarations, warnings, basic link | 4/4 assigned mutants killed; 5/23 total mutants failed C01 | Inspect C01 receipts and compiler logs | `verifiers/verifier_01_build_integrity.py` |
| CLF-C02 exact API | Default `at`, signatures, constructor access, free inequality, constness | 6/6 assigned mutants killed; 14/23 total failed C02 | Compile the call/type/free-function probes | `verifiers/verifier_02_exact_api.py` |
| CLF-C03 integration/ODR | Include guard, duplicate symbols, multi-TU calls, state isolation | 2/2 assigned mutants killed; 17/23 total failed C03 | Inspect repeated-include and multi-TU link receipts | `verifiers/verifier_03_integration_odr.py` |
| CLF-C04 formatting/observer | Padding, all canonical minutes, signed inputs, repeat stability | 2/2 assigned mutants killed; 11/23 total failed C04 | Run the 1,440-point and signed probes | `verifiers/verifier_04_formatting_observer.py` |
| CLF-C05 time properties | Construction, plus/minus, normalization, equality laws and ground truths | 8/8 assigned mutants killed; 16/23 total failed C05 | Run UBSan-backed 289/306-case sweeps | `verifiers/verifier_05_time_properties.py` |
| CLF-C06 official terminal | Authenticated protected assets and all official cases | Assigned official-only mutant killed; 17/23 total failed C06 | Inspect fixed hashes and official build/run receipt | `verifiers/verifier_06_official_terminal.py` |
| Aggregate/reward boundary | Official correctness versus exact canonical conformance | Perfect dataset control: official PASS, strict FAIL, as designed | Run once with each `--acceptance-mode` | `verifiers/run_all.py` |
| Evaluator separation | Tampered assets and unavailable compiler | 12/12 policy outcomes `INVALID`; never counted as candidate failure | Rerun both evaluator controls | `validation/validate.py` |

## Unified design

| Final policy | Best original logic retained | Best v2 logic retained | Final optimization or extension |
| --- | --- | --- | --- |
| C01 | E01 strict public compile/link | C01 language identity, C02 dependency compile, C04 implementation boundary | Three non-duplicated build stages replace several overlapping compiles |
| C02 | E01/E05 member signatures | C03 default-call and exact free-operator checks | Adds private-constructor, copy-trait, equal/unequal free-operator checks |
| C03 | E05 factory and observer isolation | C05 repeated include and multi-TU ODR linkage | One multi-TU executable covers rendering and inequality across files |
| C04 | E02 formatting boundaries, E05 const observation | C06 warning/format separation | Exhaustive 1,440 canonical values, 17 signed cases, 500 repeat observations |
| C05 | E02/E04 normalization and arithmetic | C07 whole-day, signed mutation, equality | 289 construction and 306 arithmetic combinations, explicit equality ground truths, UBSan |
| C06 | E03 complete authenticated suite | C08 identical terminal guarantee | Preserved as an independent gate with one shaping-withheld official case |

The final reference run used 6 policies, 18 kernels, and 27 executed commands. The preserved v2 reference run used 8 policies, 24 kernels, and 35 commands. Summed command duration on the same machine was 16.261 seconds for final versus 19.315 seconds for v2, a local reduction of 15.81%; command count fell 22.86%. These are receipt-derived observations under different system loads, not a controlled production latency benchmark.

## Coverage results

| Corpus or control | Official terminal | Shaping union | Strict union | Result |
| --- | ---: | ---: | ---: | --- |
| Original comparison faults | 11/14 | 13/14 | 14/14 | Preserves v2’s 100% strict coverage |
| Expanded final faults | 17/23 | 22/23 | 23/23 | No survivors |
| Canonical reference | PASS | 5/5 policies PASS | PASS | 18/18 kernels |
| Dataset official-perfect control | PASS | FAIL | FAIL | Default official mode accepts; strict mode rejects |
| Tampered protected test | INVALID | INVALID | INVALID | Evaluator fault separated |
| Missing compiler | INVALID | INVALID | INVALID | Evaluator fault separated |

The shaping and terminal counts overlap and cannot be added. Six strict-contract mutants pass official tests: no-op/reversed subtraction, missing default argument, member inequality, missing include guard, and public constructor. Conversely, F12 is intentionally absent from shaping inputs and is detected only by C06. The union, not the sum of policy failures, is the relevant coverage measure.

## Mutation-driven corrections

Two failed intermediate controls materially improved the final implementation:

1. Algebraic equality checks initially allowed two consistently wrong equality implementations to survive. Explicit adjacent-minute, adjacent-hour, and normalized-equivalence ground truths were added; both survivors then failed C05.
2. The first normalized-equivalence assertion incorrectly treated `(-1, -1)` as `23:59`; the positive reference rejected it. The oracle was corrected to `(0, -1)`, the reference returned to 3/3 C05 kernels, and the complete campaign was rerun from a new directory.

An overlap audit also removed `(201, 3001)` from C04 so the case remains withheld from shaping. A targeted rerun confirmed C01-C05 PASS and C06 FAIL before the final full campaign.

## Reward semantics

`run_all.py` defaults to `--acceptance-mode official`. Under this mode, only authenticated C06 success determines `reward_ready`; C01-C05 still produce diagnostic/shaping receipts. This accepts the dataset’s perfect alternate API implementation instead of converting canonical-style preferences into a false task failure.

`--acceptance-mode strict` requires C01-C06 to pass. Use it only when the training objective explicitly requires the pinned canonical API: private constructor, default `at(hour)`, mutating reference-returning `plus/minus`, const conversion, and namespace-scope free inequality. Both modes always invalidate tool failures, protected-asset mismatch, missing receipts, malformed receipt identity, or inconsistent cross-policy candidate hashes.

## Directly verified facts

- The final run used GCC 13.3.0 and the same protected Clock asset hashes as the original and v2 packs.
- The canonical `.meta` reference passed every policy and all 18 kernels.
- All 14 prior comparison faults and all 9 new faults failed their assigned policy and strict aggregate.
- Strict detection was 23/23; shaping detection was 22/23; terminal detection was 17/23.
- The dataset control passed official mode and failed strict mode without any `INVALID` result.
- Asset tampering and the missing compiler made all 12 affected category outcomes `INVALID`.
- Final validation summary SHA-256: `4613d7a44edfcdb8d206d705076a37e47ab05652f68e67f49ecf6d99f27c3e38`.

## Inferences and unverified boundaries

The evidence supports replacing v2 with this package for Clock shadow evaluation: it preserves the observed 14/14 strict detection, reduces repeated verifier work, strengthens semantic probes, and makes the correctness contract explicit. It does not establish an unbiased detection rate on future model outputs because 23 targeted mutants are finite and category-informed.

Unverified boundaries include other compilers, integer extremes outside the safe reference range, memory errors not exercised by these paths, hostile candidates designed to consume resources, production worker concurrency, and the effect of individual shaping rewards on RL optimization. UBSan only proves absence of observed undefined behavior on executed paths. Category failures overlap heavily after compile/link faults and are not independent labels.

## Reproduction and artifacts

- Package guide: [README.md](README.md)
- Category contracts: [`Instruction/`](Instruction/)
- Category implementations: [`Implementation/`](Implementation/)
- Aggregate runner: [`verifiers/run_all.py`](verifiers/run_all.py)
- Validation harness: [`validation/validate.py`](validation/validate.py)
- Persistent machine-readable result: [`validation/validation_summary.json`](validation/validation_summary.json)
- Final external receipts: `/tmp/clock-final-validation-20260822-v4`

Reproduce into a new empty directory:

```bash
python3 Reward_GRPO/clock_verifiers_final/validation/validate.py \
  --template-exercise-dir /path/to/pinned/clock \
  --output-dir /new/empty/clock-final-validation \
  --jobs 3
```

## Conclusion

The dominant result is complete strict detection on the 23 controlled faults with a smaller execution surface than v2 and an independently necessary official terminal gate. The remaining risk is generalization and reward calibration, so the next concrete check is a shadow run over a larger unseen Clock output set using default official reward plus recorded C01-C05 diagnostics before any shaping weights are enabled.
