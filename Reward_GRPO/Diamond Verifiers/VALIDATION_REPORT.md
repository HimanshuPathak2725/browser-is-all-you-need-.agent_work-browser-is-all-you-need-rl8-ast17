# Diamond Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | Diamond |
| Source evaluation | `execution-bank-RL-v2-think-r2/fixed26-mt2-4x-20260818` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source outcomes | pass@1 `0/4`; pass by turn 2 `0/4`; 3 context-exhausted trials |
| Validation image | `glm47-reward-grpo-bank-account@sha256:e4d1090d07cab73e5c4137637beccebe1dac0f6aa440e7d4cbfc466c4f226932` |
| Compiler | GCC `13.3.0`; existing Policy E10 evidence uses pinned Clang `18.1.3` |
| Policies and kernels | 10 policy/verifier pairs; 34 source kernels; 44 complete-campaign kernels |
| Verifier-package readiness | `READY` for the pinned canonical Diamond task |
| Live GRPO readiness | `CONDITIONALLY READY`: E05 and E06 must jointly gate semantic success; E07/E08 need authenticated bundles |
| Validation date | 2026-08-23 |

## Step 1: Replay real model outputs against the current verifier

The audit preserved both turns from all four Midband-RL-v2 Diamond trials, for eight exact candidate snapshots. The failures cover unsigned spacing underflow, filled centers, a `char`/`int` template mismatch, wrong width and glyph geometry, a no-edit response that retained the wrong API, inverted outer spacing, a warning-as-error failure, and duplicated or malformed rows.

The unchanged static replay layer E01–E06 plus E09 classified all eight snapshots as agreement-fails. There were zero missed failures, zero false restrictions, zero evaluator-invalid samples, and no source mutation; E05 and E06 rejected every semantic failure, while the auxiliary vectors retained useful compile/API partial credit where appropriate. This evidence does not justify another Diamond policy.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Source corpus | Exact Midband outputs | PASS: 8 snapshots from 4 trials; all candidate hashes pinned | Rehash `validation/cases/midband_rl_v2_*` | Manifest SHA-256 `b5e2be0bae7950fc65a38d76147d2c4c7e6586852fa1dd5d1a7ff61263eae385` |
| Trial 1 turn 1 | Unsigned spacing underflow and invalid allocation | FAIL: E05, E06, and E09 reject | Replay the saved source | Structural E01–E04 remain positive partial evidence |
| Trial 1 turn 2 | Wrong glyph placement and filled center | FAIL: E05, E06, and E09 reject | Replay the saved source | Semantic terminal boundary is reached |
| Trial 2 turn 1 | `char`/`int` `min`/`max` compile mismatch | FAIL: E01–E06 and E09 reject | Replay the saved source | Compile/API and semantic layers agree |
| Trial 2 turn 2 | Wrong width, glyph, and padding geometry | FAIL: E03, E05, E06, and E09 reject | Replay the saved source | E01/E02/E04 preserve earned credit |
| Trial 3 turn 1 | No edit; pristine task retained wrong public API | FAIL: E01–E06 and E09 reject | Replay reconstructed authenticated pristine tree | Source sample is explicitly labelled `turn-1-no-edit` |
| Trial 3 turn 2 | Inverted outer spacing | FAIL: E05, E06, and E09 reject | Replay the saved source | Geometry kernels 6A/6C/6F fail |
| Trial 4 turn 1 | Unused variable under `-Werror` and wrong geometry | FAIL: E01–E06 and E09 reject | Replay the saved source | Warning and semantic signals are both visible |
| Trial 4 turn 2 | Wrong width, duplicate rows, and glyph geometry | FAIL: E03, E05, E06, and E09 reject | Replay the saved source | No semantic survivor |
| Gap classification | Current-verifier coverage | PASS: `agreement_fail=8`; misses/restrictions `0/0` | Run `run_failure_gap_audit.py` | Receipt SHA-256 `a7bf272c75a347aab4d1128c7bf363f6be3ed52392003eb597d427155acba0a2` |

## Step 2: Protect valid implementations and keep policies focused

Three positive implementations were exercised: the canonical reference, an independent formula implementation, and a valid header-only implementation. Each passed all 31 kernels in the static replay layer, for 93/93 positive kernel decisions, showing that implementation shape, helper layout, and source-file placement are not over-restricted.

Structure validation pairs all ten nonempty policies with ten AST-valid verifiers and counts 34 candidate-source kernels plus ten authenticated bundle kernels. E07 and E08 were not fabricated for source-only candidates because they require real feedback and Aider integrity bundles; E10 retains its earlier pinned Clang validation and is not falsely represented as a GCC replay result.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Canonical reference | Perfectly formed positive control | PASS: E01–E06 and E09, 31/31 | Run `reference_positive` | Pinned `.meta/example.h/.cpp` source |
| Formula implementation | Alternate valid algorithm | PASS: 31/31 | Run `formula_positive` | Uses independent row-index computation |
| Header-only implementation | Alternate valid source layout | PASS: 31/31 | Run `header_only_positive` | Confirms no `.cpp`-shape restriction |
| Positive acceptance | Valid diversity boundary | PASS: 3 implementations × 31 kernels = 93/93 | Compare policy vectors in the control receipt | No observed false restriction |
| E07 feedback layer | Two-turn evidence | Not applicable to source-only replay | Supply authenticated generated/delivered feedback hashes | Required only when such a bundle exists |
| E08 harness layer | Response/tree/log integrity | Not applicable to source-only replay | Supply authenticated Aider bundle | Never infer bundle success from source alone |
| E10 portability layer | Host and offline Clang | Covered by prior pinned package campaign | Run host and pinned-container Clang controls | Clang `18.1.3`; three source kernels |
| Package structure | Pairing, IDs, syntax, inventory | PASS: 10/10 pairs; 34 source and 44 complete kernels | Run `run_structure_validation.py` | Receipt SHA-256 `6f0047ceb3aa23e3b0ab65cb22ec6cd581a3513c7af0deca823e2849c69353f5` |
| Protected instructions | Exact source-evaluation contract | SHA-256 `ff20bbc2d91cf1ffb8b35ffbe4715867a8e0fdec29a83bf8d9ef8a18da2d9d68` | Rehash `validation/fixed/instructions.md` | Prevents cross-task replay |

## Step 3: Reject defects and distinguish evaluator invalidity

All eight authenticated failed candidates are rejected by the terminal semantic layer. A controlled filled-interior mutation separately passes E01–E04 but fails E05, E06, and E09, demonstrating the intended reward projection: valid build and API work receive partial credit, but a hollow-diamond violation cannot receive terminal success.

Tampering with the pinned official test and removing GCC both return `INVALID`, never model `-1`. Repeating the canonical reference reproduces all seven static policy decisions and every kernel vector, and every candidate reports unchanged source hashes. The verifier therefore separates candidate failure from evaluator failure and is deterministic for the tested boundary.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Eight real defects | Authenticated evaluation failures | KILLED: 8/8 by E05/E06; additional shaped failures vary by defect | Replay `validation/cases/` | No real failure survives the semantic gate |
| Filled-interior mutant | Compile/API-correct semantic defect | E01–E04 PASS; E05/E06/E09 FAIL | Run `filled_interior_mutant` | Confirms granular reward without false success |
| Tampered official test | Evaluator-integrity fault | `INVALID`: pinned official test asset mismatch | Run invalid control | Never convert to candidate `-1` |
| Missing compiler | Infrastructure fault | `INVALID`: GCC unavailable | Run invalid control | Rerun after infrastructure recovery |
| Source immutability | Verifier side-effect control | PASS for all candidate controls and replays | Compare receipt source hashes | No candidate source changed |
| Repeatability | Independent reference replay | PASS: 7/7 policy decisions and all 31 kernel scores equal | Compare `reference_positive` and `reference_repeat` | Paths and runtime are excluded from decision comparison |
| Control receipt | Positive, mutant, invalid, and repeat evidence | PASS: 3 positives, 1 semantic mutant, 2 invalid controls, 1 repeat | Rehash saved receipt | SHA-256 `a1b038ac72a48878c1bc21ae6d1c5ff4429020550dfa0de6be88b3427f5e2e95` |

## Final conclusion

The Diamond verifier package is `READY` for the pinned canonical task, and the real-output audit supports keeping the current ten policies rather than adding context. Live GRPO is `CONDITIONALLY READY` until the reward adapter proves that E01–E04/E09 are shaped evidence, E05 and E06 jointly gate semantic success, E07/E08 run only on authenticated bundles, E10 is scheduled in its pinned Clang environment, and all `INVALID` samples are discarded rather than scored against the model.
