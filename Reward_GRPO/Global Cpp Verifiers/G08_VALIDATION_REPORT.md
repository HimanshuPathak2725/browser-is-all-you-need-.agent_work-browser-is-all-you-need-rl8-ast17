# G08 validation report — Circular Buffer and Phone Number

G08 executes four authenticated C4 probes for public-header self-containment, repeated inclusion, protected-dependency isolation, and multi-translation-unit ODR/link behavior. This campaign invoked the real G08 verifier through temporary hash-bound manifests, compiled every probe with GCC 13.3.0 and C++17 warnings as errors, and compared its structural decisions with strict-build, single-TU API-link, and task terminal checks.

The campaign passed its activation-readiness gate on both topics: 5/5 valid implementations passed, all 8 targeted and 2 supplemental structural faults reached their intended negative kernel, all 8 semantic-only faults remained structurally accepted while their terminal comparator rejected them, and 4/4 evaluator faults remained `INVALID`. This proves an incremental structural signal for these two tasks, but does not activate a manifest, run GRPO, or establish checkpoint improvement.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Positive controls | Detect false rejection and reference-shape overfitting | **5/5 passed G08 4/4:** Circular reference, two exact archived valid midband candidates, Phone reference, and a private-field rename | Run the isolated command below; inspect `category: valid` | Zero valid false rejections; both terminal comparators also passed 5/5 |
| Header self-containment | Header relies on translation-unit include order | **2/2 targeted mutants rejected** by `header-self-contained`; dependent probes also failed where the same missing type propagated | Inspect `circular-self-contained-mutant` and `phone-self-contained-mutant` | Keep overlap explicit: these two mutants create three negative kernels each, not three independent faults |
| Repeated inclusion | Public header has no effective repeated-inclusion protection | **2/2 targeted mutants rejected only by `repeated-include`** | Inspect both `repeated-include-mutant` rows | Both strict-build and single-TU API-link comparators passed, providing incremental G08-only signal |
| Protected dependency | Candidate header includes a hash-bound task/test asset | **2/2 targeted mutants rejected only by `protected-dependency`** using GCC's resolved dependency graph | Inspect both `protected-dependency-mutant` rows | Both baseline comparators and terminal checks passed, providing incremental G08-only signal without scanning comments or strings |
| Multi-TU ODR/link | Duplicate definitions or missing externally linked definitions | **2/2 targeted mutants rejected**; the Circular case is the exact archived duplicate-definition midband sample | Inspect `circular-duplicate-definitions` and `phone-odr-mutant` | G08 isolates the failure, although API/link or terminal checks also reject these cases |
| Supplemental Phone structure | Existing missing-definition and observed header-name-collision controls | **2/2 rejected** by their expected G08 boundary | Inspect the two `structural-supplemental` rows | These are controlled reconstructions, not an exact historic output replay |
| Semantic specificity | Structurally valid lifecycle/NANP behavior faults | **8/8 passed G08 4/4 and failed the task terminal comparator:** 3 Circular and 5 Phone faults | Compare `g08.status` with `task_terminal_comparator.status` | Confirms G08 remains structural and does not duplicate C6 semantics |
| Evaluator integrity | Manifest tamper, protected-file tamper, malformed C4 metadata, missing compiler | **4/4 returned `INVALID`; 0/4 became candidate `FAIL`** | Inspect `invalid_controls` | `invalid_exit_codes: [2]` preserves wrapper-level infrastructure failures; preflight hash failures intentionally occur before receipt creation |
| Repeatability and immutability | Rerun drift or verifier source mutation | **23/23 decision projections matched on a clean repeat; 23/23 candidate source digests stayed unchanged** | Compare `decision_sha256`, `repeat_decision_equal`, and `source_unchanged` | Raw receipts retain timestamps, durations, and paths; the deterministic decision projection excludes those volatile fields |
| Activation gate | Require incremental signal with no valid false rejection | **PASS / ready for manifest review:** 4 incremental cases, 0 false rejections, 0 assertion failures | Inspect `activation_gate` | Keep active GRPO manifests unchanged until task-owned commands and reward routing receive a separate review |

## Reproduction

```bash
STRANGE_ISOLATED_REPLAY=1 python3 \
  "Reward_GRPO/Global Cpp Verifiers/validation/validate_g08.py" validate \
  --output-dir /tmp/g08-validation-results
```

The recorded run used pinned Polyglot commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`. Its uncommitted machine receipt was `g08_validation_receipt.json`, SHA-256 `34e88f4a1efc4142ac9a1e7f94a3f573ab97e5918f47b14d85f4938787e5f987`; generated candidates, manifests, compiler logs, and receipts remained under `/tmp`.

## Evidence boundaries

Directly verified:

- The actual G08 executor produced 92 first-run and 92 repeat kernel decisions across 23 candidates.
- All 8 targeted structural faults reached the intended C4 kernel, and both supplemental structural controls were rejected.
- Four repeated-inclusion/protected-dependency faults passed both structural comparators and terminal behavior, proving additional signal rather than rejection parity alone.
- Circular terminal evidence uses the pinned official Catch suite. Phone terminal evidence uses the committed 12-kernel hidden curriculum source.
- Focused global-verifier tests pass 13/13; the combined global and multi-environment regression set passes 18/18.

Inferred:

- The four incremental controls are suitable shaping signals for Circular Buffer and Phone Number because they separate faults that existing strict-build/API-link checks accept. Training usefulness remains an inference until a later run.

Unverified:

- No exact historic Phone Number candidate was available; Phone fault evidence is explicitly controlled or reconstructed from the committed curriculum.
- Production worker paths, container throughput, reward weighting, active manifest registration, GRPO behavior, and pass@1 change were not tested.

The categories are mutually exclusive at the candidate level, but kernel failures can overlap within one candidate. Therefore the 16 observed negative structural kernel results must not be reported as 16 unique faults. The dominant result is narrower: G08 cleanly adds repeated-inclusion and protected-dependency coverage on both topics while preserving semantic separation and evaluator-invalid handling. The next safe step is task-manifest review, not automatic activation.
