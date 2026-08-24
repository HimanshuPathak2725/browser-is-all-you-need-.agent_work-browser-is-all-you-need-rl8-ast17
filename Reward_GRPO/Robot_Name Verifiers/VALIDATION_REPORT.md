# Robot Name Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | `robot-name` |
| Method | Real Midband outputs → current-verifier gap audit → positive/mutation/`INVALID` controls |
| Source run | `execution-bank-RL-v2-think-r2` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source evaluation | `fixed26-mt2-4x-20260818`; four independent trials, up to two Aider turns |
| Source result | Pass@1 `0/4`; pass by turn 2 `1/4` |
| Current package | 5 policies, 5 verifiers, 15 independent kernels |
| Validation environment | Offline pinned image, GCC `13.3.0`, repository mounted read-only |
| Validation date | 2026-08-23 |
| Verifier-layer readiness | `READY` |
| Live GRPO readiness | `CONDITIONALLY READY` pending independent 15-kernel reward projection |

## Step 1: Replay real model outputs against the current verifier

I recovered all eight exact Robot Name source states from the four Midband-RL-v2 trials and bound them to their original run, checkpoint, GCS root, chat/result hashes, and candidate-source hashes in `failure_gap_manifest.json`. The evidence contains seven official failures and the one successful Trial 2 repair, matching pass@1 `0/4` and pass by turn 2 `1/4`.

The complete five-policy decision agreed with every official outcome: seven agreement-fails and one agreement-pass, with zero missed failures and zero restrictions. E03 alone is not a safe reward boundary for this stochastic task: it passed Trial 4 final on this replay, but E02 uniqueness and E05 namespace progression rejected the collision-append implementation; full success therefore requires all five policy verifiers to pass.

| Saved model output | Observed defect or repair | E01 | E02 | E03 | E04 | E05 | Pack result |
|---|---|---:|---:|---:|---:|---:|---|
| Trial 1, turn 1 | `generate_name()` absent from class declaration | `[+1,+1,-1]` | `[-1,-1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 1, turn 2 | Feedback made no source change; compile defect remained | `[+1,+1,-1]` | `[-1,-1,-1]` | `[+1,-1,-1]` | `[-1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 2, turn 1 | Every position randomly letter/digit; not `AA000` | `[+1,+1,+1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[-1,+1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 2, turn 2 | Correct positional format repair; 2004 assertions passed | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | Agreement-pass |
| Trial 3, turn 1 | Random loop bounds built an undersized pool | `[+1,+1,+1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[-1,+1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 3, turn 2 | `call_once` retained premature namespace exhaustion | `[+1,+1,+1]` | `[-1,-1,-1]` | `[+1,+1,-1]` | `[-1,-1,-1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 4, turn 1 | Collision retry appended five more characters | `[+1,+1,+1]` | `[+1,+1,-1]` | `[+1,+1,-1]` | `[+1,+1,+1]` | `[-1,-1,-1]` | Agreement-fail |
| Trial 4, turn 2 | Removed an include only; collision defect remained | `[+1,+1,+1]` | `[+1,+1,-1]` | `[+1,+1,+1]` | `[+1,+1,+1]` | `[-1,+1,-1]` | Agreement-fail |

## Step 2: Protect valid implementations and decide whether another policy is needed

The pinned reference, the authentic Trial 2 successful repair, and a behavior-preserving helper rename each passed all 15 kernels. A fresh reference repeat added the fourth positive execution, producing 60/60 positive kernel passes with no candidate-source mutation and no restriction of the observed alternate-valid implementation.

The failure-gap audit showed that the current policies already map to every observed defect: E01 catches declaration/linkage, E02 catches format/reset/uniqueness, E03 authenticates the official suite, E04 checks lifecycle behavior, and E05 stresses namespace progression. Because the complete pack has zero misses and zero restrictions, adding a sixth policy would add prompt/reward complexity without failure-derived evidence.

| Control or decision | Expected boundary | Result | Evidence |
|---|---|---|---|
| Pinned reference | All five policies pass | PASS | 15/15 kernels |
| Real Trial 2 final | Accept observed alternate correct implementation | PASS | 15/15 kernels |
| Renamed private helper | Ignore non-contractual private spelling | PASS | 15/15 kernels |
| Fresh reference repeat | Preserve normalized status and vectors | PASS | 15/15 kernels |
| Source immutability | Verifiers never edit candidate bytes | PASS | All source-before/source-after hashes matched |
| New-policy decision | Add only for an observed safe-to-cover miss | KEEP CURRENT 5 | 0 misses; 0 restrictions |

## Step 3: Reject focused defects and distinguish evaluator invalidity

Three compile-clean, single-defect mutants exercised the boundaries exposed by the logs. The unchanged-reset mutant failed E02/E03/E04/E05, the malformed-prefix mutant failed E02/E03/E04/E05, and the duplicate-namespace mutant failed E02/E03/E04/E05; E01 remained positive for all three because their public API and linkage were intentionally intact.

A nonexistent compiler and a tampered official test both returned `INVALID`, never candidate `-1`. All five policies reproduced the same normalized pass status and `[+1,+1,+1]` vectors on the repeated reference, while the structural audit authenticated five policy/verifier pairs, five parseable verifiers with one source comment each, all pinned contract files, and all 15 kernels.

| Control | Intended result | Observed result | Boundary evidence |
|---|---|---|---|
| Reset preserves old name | Semantic/lifecycle rejection | KILLED | E02 `[+1,-1,+1]`; E03/E04/E05 failed |
| Prefix starts `A0` | Format rejection | KILLED | E02 `[-1,-1,-1]`; E03/E04/E05 failed |
| Namespace counter never increments | Uniqueness/progression rejection | KILLED | E02 `[+1,-1,-1]`; E03/E04/E05 failed |
| Missing compiler | `INVALID` | PASS | 5/5 policies reported `invalid` |
| Tampered official test | `INVALID` | PASS | E03 pinned-asset preflight reported `invalid` |
| Repeatability | Same normalized status/vector | PASS | 5/5 policies matched |
| Structure and fixed contract | 5 pairs; 15 kernels; pinned bytes | PASS | Receipt SHA-256 `61eff436…ddcb8f` |

## Final conclusion

The Robot Name verifier package is `READY`: its current five policies cover every failure observed in the Midband evaluation without rejecting the observed valid repair or the behavior-preserving control. No new policy or verifier was added; the audit corrected the evaluation rule so a full pass means all five policies pass, with `INVALID` dominating candidate failure.

Live GRPO integration is `CONDITIONALLY READY`: project all 15 kernels independently for shaped reward, require every policy for full reward, and discard `INVALID` samples. Do not use E03 alone, because random official execution can temporarily miss the collision-append defect that E02 and E05 expose under stronger semantic workloads.
