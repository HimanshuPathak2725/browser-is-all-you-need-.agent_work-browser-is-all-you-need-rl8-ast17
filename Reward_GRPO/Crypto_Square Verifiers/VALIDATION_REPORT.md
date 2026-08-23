# Crypto Square Verifier Validation Report

| Report field | Value |
|---|---|
| Topic | `crypto-square` |
| Verifier commit | Uncommitted scoped worktree on `56edd9767fc8426776fe3f5379c5815a18383e59` |
| Policies | 6 (`CS-E01`–`CS-E06`) |
| Kernels | 18 (3 per policy) |
| Validation date | 2026-08-23 |
| GRPO readiness | READY |

## Step 1: Structure and frozen-contract validation

All six verifier wrappers were parsed with Python AST, checked for exactly one source comment, matched one-to-one with policy documents numbered 01–06, and traced through the shared Strange execution core. The shared core uses subprocess argument lists, requires a new or empty external output directory, authenticates protected and candidate bytes with SHA-256, checks source immutability, and emits `verification_receipt.json`.

The frozen candidate boundary is only `crypto_square.h` and `crypto_square.cpp`; the official test SHA-256 is `3770199d92bda7e4551742ac2d5a30a1970318f18f92f29088f9704a6e67a676`. E03 maps the complete eight-assertion official suite and is the sole terminal policy, while E01, E02, E04, E05, and E06 are per-sample diagnostics. This upgrade changed the task-specific reward projection and validation files only; it did not change infrastructure, checkpoints, training hyperparameters, launch resources, or model-facing instructions.

| Check | Expected condition | Result | Evidence |
|---|---|---|---|
| Package structure | 6 policies, 6 matching AST-valid verifiers, one comment each | PASS | Policy/verifier numbers `1–6`; wrapper SHA-256 values recorded in control receipts |
| Frozen assets | Candidate files isolated; official assets immutable | PASS | Official test SHA-256 `3770199…e676`; tampering returned INVALID for 6/6 policies |
| Contract-to-kernel trace | Public API, normalization, sizing, segmentation, layout, safety, and all official assertions mapped | PASS | E01 API; E02/E04 properties; E03 8/8 official assertions; E05/E06 diagnostics |
| Context and execution boundary | No verifier evidence enters prompts; no infrastructure/training mutation | PASS | Audit corpus is reachable only from `validation/`; model instructions contain no policy IDs |

## Step 2: Known-good and metamorphic validation

The canonical correct candidate and an alternate-valid implementation with only private field names changed were each executed twice through all six policies in the pinned GCC 13.3.0, no-network, read-only container. The unchanged 12-kernel live verifier from commit `133713036d844268086899342f300c987649ee72` was also replayed against 49 preserved outputs selected from all 2,048 outputs of `crypto-square-kernel12-grpo20-rerun-20260821T173527Z`.

Both correct implementations returned `[+1,+1,+1]` for every policy on both repetitions. The real-output audit produced 20 agreement-passes, 24 agreement-fails, zero current-pass/official-fail misses, and five current-fail/official-pass restrictions; E05 rejected all five and E06 rejected two, so neither can be a terminal gate. An API-correct `"b"` adversary passed every diagnostic policy but failed E03, confirming that the authenticated official scorer is necessary and is present.

| Control | Scope | Result | Evidence |
|---|---|---|---|
| Canonical reference, repeated | 6 policies × 3 kernels × 2 runs | 36/36 PASS | Control receipt SHA-256 `d3ec801041d971a8ca4074a0c9c45dcc8f7d2dc64191822dd562a4e1ada9e871` |
| Private-field rename, repeated | Alternate-valid implementation, same 36 decisions | 36/36 PASS | Identical statuses and kernel vectors across repeats |
| Preserved real-output replay | 49 selected candidates from 2,048 outputs | 20 agreement-pass; 24 agreement-fail; 5 restrictions; 0 misses | Replay receipt SHA-256 `0025adc2512ed6735f5f7adc849d7d1aaf001308b1e8ad8d96116272581e8f87` |
| API-correct semantic adversary | Incorrect output only for official case `"b"` | E03 FAIL; E01/E02/E04/E05/E06 PASS | Authoritative scorer caught the diagnostic-suite survivor |

## Step 3: Mutation, INVALID, and repeatability validation

Controlled candidates covered strict API return type, punctuation normalization, an official-only branch, unspaced layout, empty-input crash, and plaintext passthrough. Evaluator-fault controls removed the compiler or changed the protected official test; every policy ran in a separate output tree, and candidate source digests were compared before and after every execution.

All five mutants proven faulty by the authoritative suite were killed by E03, the API-return mutation remained an explicitly strict diagnostic because the official suite accepts it, and both evaluator faults returned INVALID for all six policies. Positive and alternate-valid decisions repeated exactly, and source bytes remained unchanged in all 12 controls and all 49 replay cases. Failures overlap across dependent kernels and therefore are not counted as independent model errors.

| Policy | Controlled fault or invalid control | Expected | Observed |
|---:|---|---|---|
| 1 | API return-type mutation | Strict diagnostic `-1`; official may pass | `[+1,-1,-1]`; E03 PASS |
| 2 and 4 | Normalization/layout mutations | Localized `-1` without terminal authority | Both rejected the relevant mutants; official E03 remained authoritative |
| 3 | Official-only `"b"` mutation and five semantic mutants | `-1` for behavior; full official coverage | `[+1,+1,-1]`; 5/5 authoritative-suite-failing mutants killed |
| 5 | Empty-input crash | 5A/5C `-1`, unrelated 5B preserved | `[-1,+1,-1]` |
| 6 | Unspaced layout | Compact pass; geometry/padding fail | `[+1,-1,-1]` |
| 1–6 | Missing compiler and protected-test tampering | INVALID, never candidate `-1` | 12/12 policy-control combinations INVALID |
| Mutation adequacy | Five non-equivalent, official-suite-failing semantic mutants | Required authoritative rejection | 5/5 killed; no surviving terminal mutant |

## Final conclusion

The package is READY for task-specific GRPO reward consumption after a source commit pins this worktree: E03 is the sole default terminal truth, official passes receive full credit, and E01/E02/E04/E05/E06 provide non-terminal per-sample shaping only while official behavior fails. The validation is reliable because it combines a replay of preserved model outputs, correct and alternate-valid controls, mutation adequacy, evaluator-fault INVALID controls, repeatability, source immutability, and a passing local reward preflight; it does not claim a distributed reward-worker run, so the next check is a short reward-worker canary before a full GPU job. No trajectory kernel is present, and no validation evidence or policy text is model-facing. The workflow used `strange` to build, `strange-validate-verifiers` to validate, and `strange-build-validation-reports` to record the decision.
