# Kindergarten Garden verifier final validation report

The final Kindergarten Garden package contains six independently executable policies and one aggregate runner. C01-C05 cover build, dependency integrity, exact enum/API integration, roster mapping, dynamic row geometry, bounded views, repeatability, full generated behavior, and runtime safety; C06 authenticates the protected task assets and runs the complete official suite.

Kindergarten Garden was selected because the four midband-rl-v2 iter-19 evaluations recorded 0/4 pass@1 and 0/4 success by turn two, tied for the weakest remaining task. The final package rejects every tested fault, accepts every tested valid implementation, and defaults to the complete strict contract while retaining official-only mode for compatibility analysis.

| Component | Verified result | Boundary |
| --- | --- | --- |
| Canonical source | Aider Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; nine protected hashes pinned | [Pinned Kindergarten Garden source](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/cpp/exercises/practice/kindergarten-garden) |
| Iter-19 outputs | All four trials failed at both evaluated turns | Exact final `.h`/`.cpp` pairs were replayed from all four archived evaluations |
| Observed failures | 4/4 rejected | Trials 1/3 fail build/API; trials 2/4 pass C01-C02 and fail roster, geometry, oracle, and official behavior |
| Valid controls | 4/4 passed all 16 kernels | Canonical, roster lookup, direct-return implementation, and named include guard |
| Fault campaign | 35/35 rejected; zero `INVALID` fault outcomes | Four observed failures plus 31 targeted contract faults |
| Baseline comparison | Authenticated official suite rejected 23/35 | No prior Kindergarten Garden verifier pack exists locally or in Git history; C06 is the reproducible original benchmark boundary |
| Evaluator boundaries | Tampered protected asset and missing compiler both returned aggregate `INVALID` | Evaluator faults never become candidate failures or rewards |
| Reward boundary | Default `strict` requires C01-C06; `official` uses C06 only | Cross-policy candidate-source digest consistency is mandatory |

## Creation method

1. Select Kindergarten Garden from the four iter-19 receipts using measured pass rate and local evidence availability.
2. Pin the official task and independent reference solution from the Aider Polyglot commit above.
3. Recover and independently replay the four exact final checkpoint candidates.
4. Build 31 targeted faults around observed indexing failures and uncovered contract boundaries, plus four behaviorally valid controls.
5. Compare the final strict boundary with the authenticated 17-case official boundary on the same 39 candidates.
6. Consolidate overlapping checks into six policies, authenticate protected assets, preserve `FAIL` versus `INVALID`, and require source-digest consistency.

The detailed contract for each policy is in [`Instruction/`](Instruction/), and its implementation rationale is in [`Implementation/`](Implementation/).

## Validation summary

| Validation set | Final result | Official baseline |
| --- | --- | --- |
| Canonical reference | Passed 16/16 kernels | Passed 17/17 official cases |
| Valid implementations | 4/4 passed | 4/4 passed |
| Observed iter-19 failures | 4/4 rejected | 4/4 rejected |
| New targeted faults | 31/31 rejected | 19/31 rejected |
| Complete fault set | 35/35 rejected; 0 invalid | 23/35 rejected |
| Protected-asset tamper | Aggregate `INVALID` | Not a candidate failure |
| Missing compiler | Aggregate `INVALID` | Not a candidate failure |

The 12 faults accepted by the official boundary but rejected by the final strict boundary were:

- wrong enum backing type, `std::string` parameters, missing include guard, and a non-inline header definition — rejected by C02;
- hidden reference and protected test-harness dependencies — rejected by C01;
- wrong behavior limited to widths four, five, or seven, plus width-five nondeterminism — rejected by C04 and C05;
- C-string misuse of a bounded student view — rejected by C03 and C05;
- width-eight out-of-bounds behavior — rejected by C04 and C05 under safety checks.

One validation-control generator was corrected before the authoritative run: its initial newline escape produced invalid C++ in a positive fixture. The corrected v2 campaign is the only result counted above.

## Evidence boundaries

Directly verified facts are the pinned source identity, four iter-19 failures, 4/4 positive acceptance, 35/35 fault rejection, 23/35 official-baseline coverage, canonical 16/16 kernel success, and both `INVALID` controls. The campaign, canonical, tampered-asset, and missing-compiler receipt digests are respectively `2c87c2bf…1bcf`, `134ae1dc…64b9`, `912b199e…7624`, and `1e04495a…8783`.

The inference is that the consolidated strict boundary is a stronger reward signal than official-only success because it detects exact-API, integration, dependency, unseen-width, view-extent, repeatability, and safety faults. This validation does not prove an improvement in model training or generalization.

Unverified boundaries are malformed diagrams or unknown students outside the pinned contract, unseen adversarial implementations, live reward-worker ingestion, reward-weight calibration, and non-GCC portability. Policy failures overlap, so per-policy rejection totals must not be added as independent faults.

## Conclusion

The dominant compile-clean iter-19 defect is hard-coded row-stride and student-position arithmetic. The final package rejects all 35 sampled faults, accepts all four valid controls, adds 12 concrete rejections beyond the official benchmark boundary, and handles evaluator faults safely. The next production-facing check is shadow execution on unseen checkpoint outputs before enabling reward weights.
