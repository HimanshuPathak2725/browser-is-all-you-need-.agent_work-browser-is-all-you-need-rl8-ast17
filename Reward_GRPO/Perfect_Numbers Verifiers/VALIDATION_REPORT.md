# Perfect Numbers Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | `perfect-numbers` |
| Method | Real Midband outputs → current-verifier gap audit → positive/mutation/`INVALID` controls |
| Source run | `execution-bank-RL-v2-think-r2` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source evaluation | `fixed26-mt2-4x-20260818`; four independent trials, up to two Aider turns |
| Source result | Pass@1 `2/4`; pass by turn 2 `3/4` |
| Current package | 4 policies, 4 verifiers, 11 source kernels, 4 trajectory kernels |
| Validation environment | Offline pinned image, GCC `13.3.0`, repository mounted read-only |
| Validation date | 2026-08-23 |
| Verifier-layer readiness | `READY` |
| Live GRPO readiness | `CONDITIONALLY READY` pending independent reward projection and trusted E04 bundle production |

## Step 1: Replay real model outputs against the current verifier

I recovered the exact Perfect Numbers task artifacts from all four Midband-RL-v2 evaluation trials and saved six candidate snapshots: Trial 1 before and after repair, the passing Trial 2 and Trial 3 outputs, and Trial 4 before and after its harmful repair. Every snapshot is bound in `failure_gap_manifest.json` to the source run, checkpoint, GCS evaluation root, candidate hashes, and original chat/results hashes.

The combined E01–E03 source gate agreed with all six official outcomes: three agreement-passes and three agreement-fails, with zero missed failures and zero restrictions. Trial 1 initially exposed no API and then reached 13/13; Trial 4 first failed only `classify(1)` at 12/13, then changed `sum = 1` to `sum = 0`, fixed that edge, and regressed the three perfect-number cases to finish 10/13.

| Saved model output | Official outcome | E01 API | E02 semantics | E03 domain error | Terminal gate | Audit class |
|---|---:|---:|---:|---:|---:|---|
| Trial 1, turn 1 | FAIL: compile, API absent | `[-1,-1,-1,-1]` | `[-1,-1,-1,-1]` | `[-1,-1,-1]` | FAIL | Agreement-fail |
| Trial 1, turn 2 | PASS: 13/13 | `[+1,+1,+1,+1]` | `[+1,+1,+1,+1]` | `[+1,+1,+1]` | PASS | Agreement-pass |
| Trial 2, turn 1 | PASS: 13/13 | `[+1,+1,+1,+1]` | `[+1,+1,+1,+1]` | `[+1,+1,+1]` | PASS | Agreement-pass |
| Trial 3, turn 1 | PASS: 13/13 | `[+1,+1,+1,+1]` | `[+1,+1,+1,+1]` | `[+1,+1,+1]` | PASS | Agreement-pass |
| Trial 4, turn 1 | FAIL: 12/13, `classify(1)` | `[+1,+1,+1,+1]` | `[-1,+1,+1,+1]` | `[+1,+1,+1]` | FAIL | Agreement-fail |
| Trial 4, turn 2 | FAIL: 10/13, perfect cases regressed | `[+1,+1,+1,+1]` | `[+1,-1,+1,-1]` | `[+1,+1,+1]` | FAIL | Agreement-fail |

## Step 2: Protect valid implementations and keep policies focused

I replayed the pinned reference implementation and all three real Midband implementations that passed the official task. They produced 44/44 applicable source-kernel passes; a repeated reference run added 11/11 more, for 55/55 positive-control passes with no source mutation and no alternate-valid restriction.

I also constructed source-bound E04 bundles from the exact Trial 1 and Trial 4 turn snapshots and their observed test counts. The successful Trial 1 repair passed all four trajectory checks, while Trial 4 passed targeting and diagnostic removal but failed non-regression and full repair; this is the exact boundary the evaluation logs require, so no additional policy is justified.

| Control | Expected boundary | Result | Evidence |
|---|---|---|---|
| Pinned reference | E01–E03 all pass | PASS | 11/11 kernels |
| Real Trial 1 final | Accept alternate correct implementation | PASS | 11/11 kernels |
| Real Trial 2 final | Accept square-root pair implementation | PASS | 11/11 kernels |
| Real Trial 3 final | Accept formatting and local-name variation | PASS | 11/11 kernels |
| Trial 1 repair trajectory | Target edit, remove diagnostic, no regression, reach 13/13 | PASS | E04 `[+1,+1,+1,+1]` |
| Trial 4 regressing trajectory | Detect that a nominal edge repair loses earlier passing cases | KILLED | E04 `[+1,+1,-1,-1]` |
| New-policy decision | Add only for an observed miss not covered safely | KEEP CURRENT 4 | Zero misses, zero restrictions |

## Step 3: Reject focused defects and distinguish evaluator invalidity

I ran three focused compile-clean mutants through the source verifiers. E02-A alone exposed the `classify(1)` mutant, E02-B and E02-D exposed omission of divisor one, and E03 rejected `std::invalid_argument` for all zero/negative partitions while E01 and unrelated semantic kernels stayed positive.

Two evaluator faults—a nonexistent compiler and a modified official test—returned `INVALID`, never candidate `-1`. E01–E03 reproduced identical status and kernel vectors on the repeated reference, all candidate bytes remained unchanged, and the offline container had no network, no added capabilities, a read-only repository, and a separate writable receipt mount.

| Control | Intended result | Observed result | Boundary evidence |
|---|---|---|---|
| `classify(1)` returns perfect | E02-A `-1`; unrelated kernels positive | KILLED | E01 pass; E02 `[-1,+1,+1,+1]`; E03 pass |
| Proper-divisor accumulator starts at zero | E02 semantic rejection | KILLED | E02 `[+1,-1,+1,-1]` |
| Throws `std::invalid_argument` | E03 exact-type rejection | KILLED | E03 `[-1,-1,-1]` |
| Missing compiler | `INVALID` | PASS | Preflight status `invalid` |
| Tampered official test | `INVALID` | PASS | Pinned-asset status `invalid` |
| Repeatability | Same normalized status/vector | PASS | 3/3 source policies matched |
| Structure and fixed contract | 4 pairs; 15 kernels; pinned bytes | PASS | 4/4 AST, 4/4 comments, 6/6 recorded fixed hashes |

## Final conclusion

The Perfect Numbers verifier package is `READY`: the current four policies cover every failure observed in the Midband evaluation without restricting any observed valid implementation. The decisive terminal source condition is that E01, E02, and E03 all pass; no API-only or partial semantic score is a full success.

Live GRPO integration is `CONDITIONALLY READY`: project the 11 source kernels independently for shaped reward, require the combined E01–E03 gate for a full pass, discard `INVALID`, and feed E04 only source-bound trusted two-turn evaluation bundles. No verifier, policy, infrastructure, training, or launch file needed modification during this audit.
