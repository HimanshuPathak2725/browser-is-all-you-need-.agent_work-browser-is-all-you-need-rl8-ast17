# Sublist Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | `sublist` |
| Method | Real Midband outputs → current-verifier gap audit → positive/mutation/`INVALID` controls |
| Source run | `execution-bank-RL-v2-think-r2` |
| Source checkpoint | `execution-bank-RL-v2-think-r2/checkpoints/grpo_lora_r16/iter_0000019/adapter` |
| Source evaluation | `fixed26-mt2-4x-20260818`; four independent trials, up to two Aider turns |
| Source result | Pass@1 `4/4`; pass by turn 2 `4/4`; Trial 2 separately reported context metadata exhaustion after its code passed |
| Current package | 10 policies, 10 verifiers, 46 independent kernels: 36 candidate-source and 10 bundle kernels |
| Package SHA-256 | `08b590933d7a4e60e231a2e3088b5d9d1096a9d19aad54b10e63d292745a1650` |
| Workspace base commit | `56edd9767fc8426776fe3f5379c5815a18383e59` |
| Validation environments | Offline GCC `13.3.0`; host Clang `18.1.3`; immutable offline Clang `18.1.8` |
| Validation date | 2026-08-23 |
| Verifier-layer readiness | `READY` |
| Live GRPO readiness | `CONDITIONALLY READY` pending independent reward projection and trusted bundle production |

## Step 1: Replay real model outputs against the current verifier

I recovered all four authenticated Sublist task folders from the Midband-RL-v2 GCS evaluation root and saved each final candidate with hashes binding it to the chat, result receipt, run, checkpoint, task manifest, official tests, and fixed contract overlay. All four candidates passed the official 18-test suite on the first recorded test outcome; Trial 2's `num_exhausted_context_windows: 1` occurred as Aider response metadata after a semantically correct candidate was already present.

The GCC replay ran E01–E06 and E09 over each source and produced 132/132 positive kernel executions: four agreement-passes, zero verifier misses, zero restrictions, and no source mutation. E10 then passed 15/15 kernels over the four candidates plus the reference under exact host Clang 18.1.3 and another 15/15 in the immutable Clang 18.1.8 image; the GCC-only image's missing `clang++` was correctly treated as an environment `INVALID`, not candidate failure.

| Saved model output | Official evidence | E01 | E02 | E03 | E04 | E05 | E06 | E09 | E10 host/container | Classification |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Trial 1 final | 18/18; `std::search`, larger/needle helper | 5/5 | 4/4 | 5/5 | 5/5 | 6/6 | 5/5 | 3/3 | 3/3, 3/3 | Agreement-pass |
| Trial 2 final | 18/18; context metadata exhausted after valid code | 5/5 | 4/4 | 5/5 | 5/5 | 6/6 | 5/5 | 3/3 | 3/3, 3/3 | Agreement-pass |
| Trial 3 final | 18/18; explicit contiguous-window scan | 5/5 | 4/4 | 5/5 | 5/5 | 6/6 | 5/5 | 3/3 | 3/3, 3/3 | Agreement-pass |
| Trial 4 final | 18/18; `std::search`, larger/smaller helper | 5/5 | 4/4 | 5/5 | 5/5 | 6/6 | 5/5 | 3/3 | 3/3, 3/3 | Agreement-pass |

## Step 2: Protect valid implementations and decide whether another policy is needed

The positive campaign used three structurally different correct implementations: the pinned iterator-based reference, an explicit manual contiguous-window scan, and a header-only inline `std::search` implementation. All passed E01–E06 and E09, and a fresh reference repeat produced identical normalized status and kernel vectors, for 132/132 positive GCC kernel executions without changing candidate bytes.

The package is already broader than the observed need: E01–E04 cover build, warnings, exact API, and dependency ownership; E05 authenticates the complete official behavior; E06 independently checks contiguity, direction, false-start recovery, empty rules, and input preservation. With four real agreement-passes, multiple alternate-valid passes, no false restrictions, and no missed failures, adding an eleventh policy would increase reward complexity without a failure-derived boundary and is rejected.

| Control or decision | Expected boundary | Result | Evidence |
|---|---|---|---|
| Pinned iterator reference | Accept canonical valid implementation | PASS | E01–E06/E09: 33/33; E10 host/container: 3/3 each |
| Manual contiguous-window scan | Accept different control flow/private names | PASS | 33/33 GCC kernels |
| Header-only inline implementation | Accept contract-permitted layout | PASS | 33/33 GCC kernels |
| Fresh reference repeat | Preserve normalized decisions | PASS | 7/7 GCC policies and every kernel vector matched |
| Real model diversity | Accept `std::search` and explicit-loop forms | PASS | Four real candidates; 132/132 GCC kernels plus 24/24 E10 candidate kernels |
| New-policy decision | Add only for a demonstrated safe-to-cover gap | KEEP CURRENT 10 | 0 misses; 0 restrictions; no observed uncovered boundary |

## Step 3: Reject focused defects and distinguish evaluator invalidity

Three compile-clean defects targeted the historical semantic boundaries without changing the public API. Direction reversal, loose non-contiguous subsequence matching, and wrong empty-list handling were each rejected independently by both E05 and E06; the surviving sub-kernels are expected because the policies provide shaped evidence rather than duplicating one binary official-suite score.

A tampered official test and a nonexistent compiler each produced six `INVALID` E05 kernels and never candidate `-1`. The structure receipt authenticates all 10 policy/verifier pairs and all 46 kernels, the seven GCC candidate policies repeated identically on the reference, both E10 environments accepted all five valid candidates, and every replay left source hashes unchanged.

| Control | E05 vector | E06 vector | Required result | Observed result |
|---|---:|---:|---|---|
| Direction reversal | `[-1,-1,-1,-1,+1,-1]` | `[-1,-1,-1,+1,+1]` | Reject relation direction | KILLED |
| Loose subsequence instead of contiguous window | `[-1,+1,+1,+1,-1,-1]` | `[-1,-1,+1,+1,+1]` | Reject non-contiguous matching | KILLED |
| Empty needle incorrectly returns false | `[-1,-1,+1,+1,+1,-1]` | `[-1,+1,+1,+1,+1]` | Reject empty-list semantics | KILLED |
| Tampered official test | `[INVALID × 6]` | Not run | Evaluator `INVALID` | PASS |
| Missing compiler | `[INVALID × 6]` | Not run | Evaluator `INVALID` | PASS |
| Repeatability and immutability | All-positive repeat | All-positive repeat | Same decisions; no source edits | PASS |
| Structure and portability | 10 pairs, 46 kernels | Two Clang environments | Complete authenticated package | PASS |

## Final conclusion

The Sublist verifier package is `READY`. The existing 10 policies already accept every real passing Midband implementation and alternate-valid control, reject the three focused semantic defects, distinguish evaluator faults as `INVALID`, and reproduce portability under two Clang environments. No policy or verifier logic was changed and no new policy is justified.

Live GRPO integration is `CONDITIONALLY READY`: use E01–E06 as independent per-candidate reward signals, require E05 and E06 for semantic full credit, and discard any `INVALID`. Keep E07–E08 as trusted trajectory/harness audits and E09–E10 as periodic safety/promotion gates rather than placing their policy text in the prompt or executing expensive toolchain checks on every rollout; this preserves signal without context pollution or over-restriction.
