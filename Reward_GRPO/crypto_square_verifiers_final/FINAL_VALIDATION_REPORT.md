# Crypto Square verifier final validation report

The final Crypto Square package contains six independently executable policies and one aggregate runner. C01-C05 cover build, dependency integrity, exact API integration, normalization, dimensions, segments, full cipher behavior, repeatability, and runtime safety; C06 authenticates the protected task assets and runs the complete official suite.

Crypto Square was selected after Diamond because the four midband-rl-v2 iter-19 evaluations recorded 1/4 pass@1 and 1/4 success by turn two, the next-weakest measured task. The final package rejects every tested fault, accepts every tested valid implementation, and defaults to the complete strict contract while retaining official-only mode for compatibility analysis.

| Component | Verified result | Boundary |
| --- | --- | --- |
| Canonical source | Aider Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; nine protected hashes pinned | [Pinned Crypto Square source](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/cpp/exercises/practice/crypto-square) |
| Iter-19 outputs | Trial 4 passed; trials 1-3 failed | Exact final `.h`/`.cpp` pairs were replayed from all four archived evaluations |
| Observed failures | 3/3 rejected | Trials 1 and 3 fail build/API boundaries; trial 2 passes C01-C03 and fails segments, full oracle, and official behavior |
| Valid controls | 4/4 passed all 16 kernels | Canonical reference, iter-19 trial 4, private-field rename, and reserve-only rewrite |
| Fault campaign | 34/34 rejected; zero `INVALID` fault outcomes | Three observed failures plus 31 targeted contract faults |
| Original comparison | Original CS-E01-E04 union rejected 28/34 | The final set closes six measured gaps while preserving all original rejections |
| Evaluator boundaries | Tampered protected asset and missing compiler both returned aggregate `INVALID` | Evaluator faults never become candidate failures or rewards |
| Reward boundary | Default `strict` requires C01-C06; `official` uses C06 only | Cross-policy candidate-source digest consistency is mandatory |

## Creation method

1. Select Crypto Square from the four iter-19 receipts using measured pass rate.
2. Pin the official task and independent reference solution from the Aider Polyglot commit above.
3. Recover the four exact final checkpoint candidates and diagnose their build, API, normalization, segmentation, layout, and terminal behavior.
4. Build 31 targeted faults around the observed failures and uncovered contract boundaries, plus four behaviorally valid controls.
5. Compare the final policies with all four original Crypto Square policies on the same 38 candidates.
6. Consolidate overlapping checks into six policies, authenticate protected assets, preserve `FAIL` versus `INVALID`, and require source-digest consistency.

The detailed contract for each policy is in [`Instruction/`](Instruction/), and its implementation rationale is in [`Implementation/`](Implementation/).

## Validation summary

| Validation set | Final result | Original comparison |
| --- | --- | --- |
| Canonical reference | Passed 16/16 kernels | Passed 12/12 original kernels |
| Valid implementations | 4/4 passed | 4/4 passed all original policies |
| Observed iter-19 failures | 3/3 rejected | 3/3 rejected |
| New targeted faults | 31/31 rejected | Original union rejected 25/31 |
| Complete fault set | 34/34 rejected; 0 invalid | Original CS-E01-E04 union rejected 28/34 |
| Protected-asset tamper | Aggregate `INVALID` | Not a candidate failure |
| Missing compiler | Aggregate `INVALID` | Not a candidate failure |

The six faults accepted by every original policy but rejected by the final strict boundary were:

- hidden reference include and protected test-harness dependency — rejected by C01;
- length-255 out-of-bounds behavior and a wrong result limited to length 17 — rejected by C05;
- missing include guard — rejected by C02;
- an invalid empty plaintext segment — rejected by C04 and C05.

One positive-control generator was corrected during validation: its initial global private-field rename also changed the required `plain_text_segments` method name. The corrected token-scoped rename preserves the public API and passes all final and original policies, so the invalid fixture is not counted as verifier coverage.

## Evidence boundaries

Directly verified facts are the pinned source identity, four iter-19 outcomes, 4/4 positive acceptance, 34/34 fault rejection, 28/34 original-policy union coverage, canonical 16/16 kernel success, and both `INVALID` controls. The campaign, canonical, tampered-asset, and missing-compiler receipt digests are respectively `000824dc…a3cf`, `008be643…196e`, `4645957d…a405`, and `496c34ea…0368`.

The inference is that the consolidated strict boundary is a stronger reward signal than official-only success because it detects dependency, include-idempotence, empty-boundary, safety, and broader-domain faults missed by all original policies. This validation does not prove an improvement in model training or generalization.

Unverified boundaries are unseen adversarial implementations, live reward-worker ingestion, reward-weight calibration, and non-GCC portability. Policy failures overlap, so per-policy rejection totals must not be added as independent faults.

## Conclusion

The dominant successful-build iter-19 defect is incorrect row segmentation and transposed layout. The final package rejects all 34 sampled faults, accepts all four valid controls, adds six concrete rejections beyond the original policy union, and handles evaluator faults safely. The next production-facing check is shadow execution on unseen checkpoint outputs before enabling reward weights.
