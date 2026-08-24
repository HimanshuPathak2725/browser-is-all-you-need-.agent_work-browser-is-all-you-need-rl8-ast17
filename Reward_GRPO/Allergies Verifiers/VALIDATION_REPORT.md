# Allergies Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | Allergies |
| Source evaluation | `execution-bank-RL-v2-think-r2/fixed26-mt2-4x-20260818` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source outcomes | pass@1 `3/4`; pass by turn 2 `4/4` |
| Validation image | `glm47-reward-grpo-bank-account@sha256:e4d1090d07cab73e5c4137637beccebe1dac0f6aa440e7d4cbfc466c4f226932` |
| Compiler | GCC `13.3.0` |
| Policies and kernels | 6 policies; 11 candidate kernels plus 5 two-turn kernels |
| Verifier-package readiness | `READY` for the pinned canonical Allergies task |
| Live GRPO readiness | `CONDITIONALLY READY`: reward wiring must require terminal E06 and supply E05 only authenticated two-turn bundles |
| Validation date | 2026-08-23 |

## Step 1: Replay real model outputs against the current verifier

The audit saved the exact editable sources from all four Midband-RL-v2 Allergies trials: the failed first turn and repaired second turn from trial 1, plus the passing first turns from trials 2–4. Their source bytes, evaluation-chat hashes, result hashes, checkpoint, Aider controls, and GCS archive are pinned in `failure_gap_manifest.json`; perfectly formed sources were not used as negative evidence.

The finalized E01–E04 diagnostic pack and E06 official gate agreed on all five snapshots: four agreement-passes and one agreement-fail, with zero missed failures and zero restrictions. The failed source lacked `<unordered_map>`; the original E05 classified that valid repair evidence as `INVALID`, so E05 was extended only for the exact authenticated `build.missing_unordered_map_include` class while retaining its prior enum-parameter class.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Source corpus | Real Midband outputs, not generated templates | PASS: 5 source snapshots from 4 trials; hashes match manifest | Rehash each `cases/midband_rl_v2_*` source | `validation/failure_gap_manifest.json` |
| Trial 1 turn 1 | Missing standard-library include | FAIL in diagnostic pack and E06 | Replay E01–E04 and E06 | Compiler reports `std::unordered_map` missing and names `<unordered_map>` |
| Trial 1 turn 2 | Feedback repair | PASS in diagnostic pack and E06; 50/50 assertions | Replay saved repaired source | Only required include changed |
| Trials 2–4 | Independent positive outputs | PASS: 3/3 in diagnostic pack and E06 | Replay saved first-turn sources | Structurally different implementations remain accepted |
| Gap classification | Missed-failure and restriction check | PASS: `agreement_pass=4`, `agreement_fail=1`, `missed_failure=0`, `restriction=0` | Run `run_failure_gap_audit.py` in pinned image | Receipt SHA-256 `ff7c6cb7107cc2dd406c995163603d0a442372849706deb8fb22147e115d6c08` |
| E05 baseline | Previous two-turn classifier | `INVALID` on the real missing-include repair | Run old and current E05 on identical hash-bound bundle | Baseline SHA-256 `96bb2af9…0150f` |
| E05 correction | Exact new repair boundary | PASS `+5/5`; no arbitrary compiler-error match | Inspect declared/observed repair class and all five kernels | Current E05 SHA-256 `4f0768b9d489f6d5a2d3d79d07fa78062fcf6604d947c992d4358c1c80740d0d` |

## Step 2: Protect valid solutions and remove over-restriction

The positive-control campaign ran the official reference, a private-field rename, and a behaviorally valid `char const*` parameter implementation through E01–E04 and all 50 official assertions. The first two passed immediately; the alternate API passed E06 but initially failed E02, proving that the old exact-`std::string const&` rule was reference-shape restriction rather than an official task requirement.

E02 was narrowed to accept either `std::string const&` or `char const*`, while its non-const and const string-literal probes still reject the observed enum-only API. After the correction, all three valid controls pass every candidate policy and E06, and the enum-parameter candidate still fails E02 and E06; no private names, map representation, overload count, or source shape is rewarded.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Reference positive | Perfectly formed positive control | PASS: E01–E04 and E06; 50/50 assertions | Run `reference_positive` | `validation/control_validation_receipt.json` |
| Private-field rename | Alternate implementation shape | PASS: E01–E04 and E06; 50/50 | Rename `result` to `stored_score` and replay | Confirms private representation is not scored |
| C-string alternate | Official-valid non-reference API | Initially E02 FAIL/E06 PASS; post-fix all PASS | Run `c_string_parameter_alternate` | This control directly caused the E02 relaxation |
| Enum parameter | Real historical API failure | E02 FAIL and E06 FAIL | Run `enum_parameter_drift` | Prevents the relaxation from reopening the logged failure |
| E02 post-fix identity | Anti-restriction correction | SHA-256 `72989ab60da82292affc12eab06247124725dfe55fa1f4d90ca9ea6ce5216a2d` | Inspect 2A–2C probes and policy | `policy_02_specific_allergy_string_api.md`; `verifier_02_*.py` |
| Positive-control result | Valid-candidate acceptance | PASS: 3/3 control implementations × 5 policies | Compare normalized statuses | Control receipt SHA-256 `17d707c86595c86b31ba479e78cce2400d3364e6356c77b3948c11d0f375e824` |
| Structure | Policy/verifier pairing and kernel inventory | PASS: 6/6 pairs, 11 candidate + 5 trajectory kernels, all AST parses, one source comment each | Run `run_structure_validation.py` | Receipt SHA-256 `1f8ced968e30921dd107e1a980b6d4b22ae06c702f02dc86322ac10f272add18` |

## Step 3: Reject defects and separate candidate failure from invalid evidence

Four targeted candidate defects exercised the logged boundaries: namespace drift, enum parameter drift, return-container drift, and signedness warning. Their intended diagnostic policy fails and E06 also fails. An API-correct implementation returning only `false` and an empty set passes E01–E04 but fails E06, demonstrating that the diagnostic kernels are useful partial rewards but cannot replace the protected official terminal gate.

E05 accepts the real Midband repair at `+5/5` and still recognizes the authenticated legacy enum-parameter diagnostic. A repeated post-feedback diagnostic is `FAIL`; altered delivered feedback and an unknown repair class are `INVALID`; a single-turn sample is `NOT_APPLICABLE`. E06 likewise returns `INVALID` for a changed official test asset or unavailable compiler, so evaluator faults never become negative model reward.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Namespace mutant | Wrong canonical type boundary | E01 FAIL; E06 FAIL | Run `namespace_drift` | Targeted control |
| Enum-parameter mutant | Logged string-literal incompatibility | E02 FAIL; E06 FAIL | Run `enum_parameter_drift` | Targeted control |
| Return-type mutant | `vector<string>` instead of string set | E03 FAIL; E06 FAIL | Run `return_type_drift` | Targeted control |
| Warning mutant | Signed/unsigned comparison under `-Werror` | E04 FAIL; E06 FAIL | Run `signedness_warning` | Targeted control |
| Semantic adversary | Correct API, false/empty behavior | E01–E04 PASS; E06 FAIL | Run `semantic_false_empty` | Proves E06 is mandatory terminal reward |
| E06 evaluator faults | Tampered test or missing compiler | `INVALID` for 2/2 controls | Run invalid controls | Never project as candidate `-1` |
| E05 successful repair | Real Midband turn 1→2 | PASS `+5/5` | Run current E05 on hash-bound bundle | Receipt includes all kernel evidence |
| E05 failed repair | Diagnostic persists after feedback | FAIL; 2 passed and 3 failed kernels; sum `-1` | Run `persistent_diagnostic` | Candidate failure, not evaluator invalidity |
| E05 evidence faults | Feedback differs or repair class unknown | `INVALID` for both controls | Run authenticated mutations | No reward emitted |
| E05 applicability | No feedback event | `NOT_APPLICABLE` for single turn | Run single-turn manifest | E05 excluded from ordinary candidate scoring |
| Legacy E05 class | Prior enum-parameter feedback | PASS: exact request and diagnostic hashes authenticate | Reclassify saved Luna diagnostic | Source request SHA-256 `9603b0f8…2581` |
| E05 campaign result | Real repair plus evidence controls | All expected decisions match | Run `run_trajectory_validation.py` | Receipt SHA-256 `8d867fc47b186762ec827ed25994d028fc0d59dcd32a49496160621bcfa2f2a7` |

## Final conclusion

The Allergies verifier package is `READY` for the pinned canonical task: real failed outputs were replayed first, valid implementation diversity is protected, targeted failures are detected, and evaluator faults remain `INVALID`. For GRPO it is `CONDITIONALLY READY` until the live reward adapter is separately proven to use E01–E04 only as shaped signals, require E06 for terminal success, and invoke E05 only when an authenticated two-turn bundle exists; no infrastructure, training, or launch file was changed by this validation work.
