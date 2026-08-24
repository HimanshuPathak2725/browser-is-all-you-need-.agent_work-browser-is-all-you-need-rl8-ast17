# D&D Character verifier final validation report

The final D&D Character package contains six independently executable policies and one aggregate runner. DNF-C01 through DNF-C05 cover strict build integrity, protected-dependency isolation, exact API and ODR integration, the complete modifier table, four-dice/drop-lowest distribution, six character rolls, hit-point derivation, and runtime safety. DNF-C06 authenticates the pinned task and runs the complete official suite.

D&D Character was selected as a measured midband problem: the four midband-rl-v2 iter-19 evaluations recorded `2/4` pass@1 and `3/4` success by turn two. The final strict package rejects every tested fault, accepts every tested valid implementation, and retains official-only mode for compatibility analysis.

| Component | Verified result | Boundary |
| --- | --- | --- |
| Canonical source | Aider Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; nine protected hashes pinned | [Pinned D&D Character source](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/cpp/exercises/practice/dnd-character) |
| Iter-19 outputs | `2/4` first-turn passes; one repair; one terminal failure | Trial 2 initially summed all four dice; trial 3 first truncated negative modifiers and ended with non-inline header ODR failures |
| Post-training outputs | Two valid endpoints accepted; one failed endpoint rejected | Failed repeat used a score-minus-11 modifier and remained incorrect after feedback |
| Valid controls | 8/8 passed all 16 kernels | Canonical, five checkpoint-valid endpoints, integer-floor source alternative, and inline-header alternative |
| Fault campaign | 27/27 cases rejected; zero `INVALID` fault outcomes | Four observed model failures plus 23 targeted contract cases |
| Original pack comparison | 20/27 rejected on the identical corpus | Seven faulty generators/integrations survived the prior four-policy boundary |
| Official baseline | 18/27 rejected on the identical corpus | Nine range-valid but contract-invalid cases passed the complete official suite |
| Evaluator boundaries | Tampered protected asset and missing compiler both returned aggregate `INVALID` | Evaluator faults never become candidate failures or rewards |
| Reward boundary | Default `strict` requires DNF-C01 through DNF-C06; `official` uses DNF-C06 only | Cross-policy candidate-source digest consistency is mandatory |

## Creation method

1. Select D&D Character using the measured iter-19 pass rate and confirm the pinned task/reference identity.
2. Recover the exact four original checkpoint trajectories and three available post-D&D-training trajectories.
3. Diagnose the real failures: sum-all-four dice, signed truncation, header ODR breakage, and score-minus-11 arithmetic.
4. Replay eight valid implementations and build 23 targeted cases around API, modifier, dice-distribution, character-independence, hit-point, dependency, and integration boundaries.
5. Run the original verifier pack, authenticated official suite, and final strict package on the same corpus.
6. Consolidate overlapping checks into six policies, preserve `FAIL` versus `INVALID`, and require cross-policy source-digest consistency.

Each consolidated contract and its implementation rationale is in [`Verifier implementation policy/`](Verifier%20implementation%20policy/).

## Validation summary

| Validation set | Final strict | Original pack | Official baseline |
| --- | ---: | ---: | ---: |
| Canonical reference | 16/16 kernels passed | Passed | 24/24 assertions passed |
| Valid implementations | 8/8 accepted | 8/8 accepted | 8/8 accepted |
| Fault cases | 27/27 rejected | 20/27 rejected | 18/27 rejected |
| Fault cases marked `INVALID` | 0 | 0 | 0 |
| Protected-asset tamper | `INVALID` | `INVALID` | `INVALID` |
| Missing compiler | `INVALID` | `INVALID` | `INVALID` |

The seven cases accepted by the original package but rejected by the final strict boundary were:

- a constant ability generator and an alternating-extremes generator;
- uniform `[3,18]` and three-dice generators;
- a constructor that copied one roll into all six fields;
- a constructor that hard-coded six different in-range fields;
- a header without an include guard.

DNF-C04 rejects the four incorrect dice distributions. DNF-C05 rejects copied or hard-coded character fields. DNF-C02 rejects the repeated-include failure. Relative to the original pack, the official suite also accepted the intermittent out-of-range generator and the wrong-member-type case. This brings the final package's measured gain to nine cases over official-only acceptance.

Policy rejection counts overlap and must not be added: DNF-C01 rejected 10/27 cases, DNF-C02 17/27, DNF-C03 11/27, DNF-C04 14/27, DNF-C05 21/27, and DNF-C06 18/27.

## Evidence boundaries

Directly verified facts are the pinned source identity, iter-19 `2/4 → 3/4` result, eight valid acceptances, 27/27 final fault rejections, 20/27 original-pack rejections, 18/27 official rejections, canonical 16/16 kernel success, and both aggregate `INVALID` controls.

The inference is that strict acceptance is a materially stronger reward boundary because it closes all seven observed same-corpus gaps in the original pack and nine gaps in the official suite. This validation does not prove improved model training or generalization.

Unverified boundaries are unseen adversarial random generators, statistical behavior on platforms with a materially different random implementation, live reward-worker ingestion of this final package, reward-weight calibration, and non-GCC portability. Statistical policies use broad thresholds but remain probabilistic; production should monitor rare rerun disagreement and neutralize it rather than charge it to the model.

## Conclusion

The dominant semantic gap was not ordinary range checking but whether `ability()` actually implements the fair four-dice/drop-lowest distribution and whether `Character` performs six generations. The final package accepts all eight valid controls, rejects all 27 fault cases, adds seven concrete rejections over the previous verifier, and safely separates evaluator faults from candidate failures.
