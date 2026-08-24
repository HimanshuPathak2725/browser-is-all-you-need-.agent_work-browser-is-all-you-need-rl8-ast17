# Diamond verifier final validation report

The final Diamond package contains six independently executable policies and one aggregate runner. C01-C05 cover build, API, integration, shape, state, geometry, full-domain bytes, and runtime safety; C06 authenticates the protected task assets and runs the complete official suite.

Diamond was selected because the four midband-rl-v2 iter-19 evaluations recorded 0/4 pass@1 and 0/4 success by turn two, the weakest observed task. The final package now rejects every tested fault, accepts every tested valid implementation, and defaults to the complete strict contract while retaining official-only mode for compatibility analysis.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| Canonical source | Freeze the task and independent solution basis | PASS: Aider Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; nine protected hashes pinned | Compare the local task assets with the pinned commit and `_contract.py` | [Pinned Aider Diamond source](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/cpp/exercises/practice/diamond); `verifiers/_contract.py` |
| Iter-19 selection | Choose the weakest measured topic without assumption | VERIFIED: four trials, 0/4 pass@1 and 0/4 by turn two | Re-read the four iter-19 run receipts | Keep Diamond first; Crypto Square is the next measured weak task |
| Observed failures | Real checkpoint failure coverage | PASS: 4/4 final candidates rejected; all failed C04-C06 and 3/4 also failed C03 | Replay the archived final `diamond.h`/`diamond.cpp` pairs in strict mode | Dominant pattern is compile-clean but incorrect geometry |
| Valid controls | Guard against reference-shape overfitting | PASS: 5/5 implementations and all 16 kernels per implementation | Run canonical, three metamorphic implementations, and the legal no-`#pragma once` header | Preserve behavior-based include idempotence |
| Fault campaign | Exercise observed and contract-level defects | PASS: 31/31 rejected, 0 `INVALID` fault outcomes | Run 13 prior mutants, four iter-19 failures, and 14 new targeted faults | Campaign summary SHA-256 `a6d46737…c686` |
| Original comparison | Check retained coverage fairly | Original P05-P06 rejected 28/31; P03-P04 rejected the three survivors; combined P03-P06 coverage is 31/31 | Run P05-P06 on all faults, then P03-P04 on the three survivors and five positives | This is a source-policy union, not a rerun of bundle/container Policies 7-10 |
| Evaluator boundaries | Separate bad candidates from bad evidence | PASS: altered protected asset and missing compiler both returned aggregate `INVALID`; canonical reference passed 16/16 | Repeat the three boundary runs with new output directories | `INVALID` always disables reward |
| Reward boundary | Prevent narrow official examples from accepting incomplete solutions | Default `strict` requires C01-C06; `official` uses C06 only for compatibility analysis | Inspect `acceptance_mode`, `reward_ready`, and per-policy statuses in the aggregate receipt | Shadow strict rewards on unseen outputs before production weighting |

## Creation method

1. Select Diamond from the four iter-19 receipts using measured pass rate.
2. Pin the official task and reference solution from the Aider Polyglot benchmark commit above.
3. Recover the four exact final checkpoint candidates and group their failures by build, API, dimensions/state, geometry, and terminal behavior.
4. Extend the prior 13 semantic mutants with 14 targeted faults and five independent positive controls.
5. Compare the final policies with the original source-policy boundary, then consolidate overlapping checks into six policies.
6. Authenticate protected assets, preserve `FAIL` versus `INVALID`, and require cross-policy candidate-source digest consistency.

The detailed contract for each policy is in [`Instruction/`](Instruction/), and its implementation rationale is in [`Implementation/`](Implementation/).

## Validation summary

| Validation set | Final result | Original comparison |
| --- | --- | --- |
| Canonical reference | Passed 16/16 kernels | Passed relevant original source policies |
| Valid alternatives | 5/5 implementations passed | 5/5 passed original P03-P06 controls |
| Prior semantic mutants | 13/13 rejected | Covered by original semantic union |
| Observed iter-19 failures | 4/4 rejected | 4/4 rejected by original P05-P06 |
| New targeted faults | 14/14 rejected | Original P05-P06 missed three structural faults; P03-P04 rejected those three |
| Complete fault set | 31/31 rejected; 0 invalid | Original P03-P06 union also 31/31 |
| Protected-asset tamper | Aggregate `INVALID` | Not a candidate failure |
| Missing compiler | Aggregate `INVALID` | Not a candidate failure |

One corpus label was corrected during validation: removing `#pragma once` from the declaration-only reference header remains legal and repeated-inclusion safe. It was moved from the fault set to the positive controls, and a real protected test-harness dependency replaced it. This prevents a false rejection from being counted as coverage.

## Evidence boundaries

Directly verified facts are the pinned source identity, the four iter-19 outcomes, 5/5 positive acceptance, 31/31 fault rejection, original P03-P06 union coverage, canonical 16/16 kernel success, and both `INVALID` controls. The campaign, canonical, tampered-asset, and missing-compiler receipt digests are respectively `a6d46737…c686`, `ee980c28…00fd`, `755fea38…d9b7`, and `215ac841…0b82`.

The inference is that the consolidated strict boundary is a cleaner reward signal than official-only success because it detects intermediate-letter, exact-API, and protected-dependency faults. This validation does not prove an improvement in model training or generalization.

Unverified boundaries are unseen or deliberately adversarial implementations, live reward-worker ingestion, reward-weight calibration, and non-GCC portability. The original comparison intentionally covers source Policies 3-6; conversation-bundle Policies 7-8 and portability/audit Policies 9-10 were not part of this per-candidate comparison.

Policy failures overlap. Per-policy rejection totals must not be added, and the original 31/31 union is established by P05-P06 over all faults plus P03-P04 over their three survivors, not by treating policy outcomes as independent samples.

## Conclusion

The dominant iter-19 Diamond failure is compile-clean but incorrect geometry. The final package rejects all 31 sampled faults, accepts all five valid controls, preserves the original source-policy union coverage, and handles evaluator faults safely; the next concrete check is shadow execution on unseen checkpoint outputs before enabling production reward weights.
