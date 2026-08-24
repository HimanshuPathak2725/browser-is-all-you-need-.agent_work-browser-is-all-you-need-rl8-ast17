# Spiral Matrix Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | `spiral-matrix` |
| Method | Real Midband outputs → current-verifier gap audit → positive/mutation/`INVALID` controls |
| Source run | `execution-bank-RL-v2-think-r2` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source evaluation | `fixed26-mt2-4x-20260818`; four independent trials, up to two Aider turns |
| Source result | Pass@1 `2/4`; pass by turn 2 `2/4` |
| Current package | 5 policies, 5 verifiers, 15 independent kernels |
| Validation environment | Offline pinned image, GCC `13.3.0`, repository mounted read-only |
| Validation date | 2026-08-23 |
| Verifier-layer readiness | `READY` |
| Live GRPO readiness | `CONDITIONALLY READY` pending independent 15-kernel reward projection |

## Step 1: Replay real model outputs against the current verifier

I recovered the exact Spiral Matrix artifacts from all four Midband-RL-v2 trials and reconstructed six evaluated source states from the authenticated chats: Trial 1 before and after its header fix, the passing Trial 2 source, Trial 3 before and after an empty repair turn, and the passing Trial 4 source. The manifest binds those files to candidate hashes, source chat/results hashes, the run, checkpoint, and GCS root.

The complete five-policy pack agreed with all six official outcomes: four agreement-fails and two agreement-passes, with zero missed failures and zero restrictions. Trial 1 first omitted `<cstdint>`, then exposed unsigned reverse-loop underflow; Trial 3 independently produced the same size-2 SIGSEGV and could not repair it before context exhaustion, while signed `int` and `int64_t` variants passed all kernels.

| Saved model output | Official evidence | E01 | E02 | E03 | E04 | E05 | Pack result |
|---|---|---:|---:|---:|---:|---:|---|
| Trial 1, turn 1 | Header cannot resolve `uint32_t`; compile fails | `[-1,-1,-1]` | `[-1,-1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 1, turn 2 | Size 2 SIGSEGV; 2/3 assertions before crash | `[+1,+1,-1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 2, turn 1 | Signed bounds; 6/6 assertions passed | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | Agreement-pass |
| Trial 3, turn 1 | Size 2 SIGSEGV; 2/3 assertions before crash | `[+1,+1,-1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 3, turn 2 | Context exhausted; source and crash unchanged | `[+1,+1,-1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 4, turn 1 | Signed 64-bit bounds; 6/6 assertions passed | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | Agreement-pass |

## Step 2: Protect valid implementations and decide whether another policy is needed

The pinned reference, both authentic passing Midband implementations, and a behavior-preserving coordinate/direction rename passed all 15 kernels. A fresh reference repeat raised the total to 75/75 positive kernel executions with no candidate-source mutation and demonstrated that `int`, `int64_t`, tuple-based, and renamed-private-local implementations remain accepted.

The current policies already provide failure-derived separation: E01 catches standalone-header/API/link issues, E02 checks exact small matrices and extended oracle behavior, E03 authenticates the official suite, E04 isolates the observed size-2 boundary, and E05 adds extended oracle and sanitizer execution. Zero observed misses and restrictions means a sixth policy would add reward/prompt complexity without evidence.

| Control or decision | Expected boundary | Result | Evidence |
|---|---|---|---|
| Pinned tuple-based reference | All five policies pass | PASS | 15/15 kernels |
| Real Trial 2 signed-`int` source | Accept observed valid implementation | PASS | 15/15 kernels |
| Real Trial 4 signed-`int64_t` source | Accept observed valid implementation | PASS | 15/15 kernels |
| Renamed coordinates/directions | Ignore non-contractual private spelling | PASS | 15/15 kernels |
| Fresh reference repeat | Preserve normalized status and vectors | PASS | 15/15 kernels |
| New-policy decision | Add only for an observed safe-to-cover miss | KEEP CURRENT 5 | 0 misses; 0 restrictions |

## Step 3: Reject focused defects and distinguish evaluator invalidity

Three compile-clean focused mutants exercised separate semantic boundaries. Returning `{{1}}` for size zero failed the empty/small kernels, counterclockwise rotation failed official and extended-oracle checks, and converting signed traversal bounds back to unsigned reproduced the exact reverse-loop underflow class from Trials 1 and 3; every mutant was rejected by the complete pack.

A nonexistent compiler and a tampered official test both returned `INVALID`, never candidate `-1`. All five policies reproduced the same normalized `[+1,+1,+1]` reference vectors, candidate bytes remained unchanged, and the structural audit authenticated five policy/verifier pairs, five parseable one-comment verifiers, all pinned fixed assets, and all 15 kernels.

| Control | Intended result | Observed result | Boundary evidence |
|---|---|---|---|
| Size zero returns singleton | Empty/small boundary rejection | KILLED | E02 `[-1,+1,+1]`; E03/E04/E05 failed |
| Counterclockwise turn | Spiral-order rejection | KILLED | E02/E03/E04/E05 failed |
| Unsigned reverse traversal | Bounds/crash rejection | KILLED | E02/E03/E04/E05 failed |
| Missing compiler | `INVALID` | PASS | 5/5 policies reported `invalid` |
| Tampered official test | `INVALID` | PASS | E03 pinned-asset preflight reported `invalid` |
| Repeatability and immutability | Same vectors; no source edits | PASS | 5/5 matched; all hashes stable |
| Structure and fixed contract | 5 pairs; 15 kernels; pinned bytes | PASS | Receipt SHA-256 `06cbe5ec…db2399a` |

## Final conclusion

The Spiral Matrix verifier package is `READY`: the existing five policies cover every Midband failure without rejecting the two observed correct implementations or the behavior-preserving control. No policy or verifier needed modification; all five policies must pass for full success and any `INVALID` result invalidates the sample.

Live GRPO integration is `CONDITIONALLY READY`: project the 15 kernels independently for shaped reward, require the complete pack for full reward, and discard `INVALID`. Keep E04’s size-2 signal and E05’s sanitizer signal independent so the model receives precise feedback instead of one opaque crash score.
