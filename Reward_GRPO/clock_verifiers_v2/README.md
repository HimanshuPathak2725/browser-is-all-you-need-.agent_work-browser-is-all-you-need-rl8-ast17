# Clock verifier package v2

This package turns the observed Clock SFT failure taxonomy into category-level GRPO signals without confusing partial progress with task correctness. Candidate source flows through eight source verifiers; the ninth tool compares before/after receipts for repair analysis. Every source verifier authenticates the pinned Clock assets and writes a machine-readable receipt outside the candidate tree.

The package is additive: it does not modify `Reward_GRPO/Clock Verifiers`. Category results can overlap, evaluator faults are `INVALID`, and standalone success requires the authenticated official terminal verifier to pass. The package is pinned to Polyglot `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` and GCC 13.3.

## Primary evidence table

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| C01 language mode | Reject non-C++17 syntax and strict-build failures | a2 emitted C++20 `<=>` | Run verifier 01 | `Instruction/01_*`, `Implementation/01_*` |
| C02 dependency completeness | Require self-contained header and declared standard-library facilities | a4 omitted `<iomanip>` | Run verifier 02 | `Instruction/02_*`, `Implementation/02_*` |
| C03 exact API/operators | Freeze every public signature, including free `operator!=` | a4 changed its form; a8 deleted it | Run verifier 03 | Closes the original CL-E01/CL-E05 gap |
| C04 header/source consistency | Ensure declarations, state-dependent definitions, and caller linkage agree | a5 omitted constructors and `_minute` | Run verifier 04 | External caller plus implementation build |
| C05 ODR/linkage | Reject duplicate and missing cross-TU symbols | a8 first attempt duplicated `operator!=` | Run verifier 05 | Two independent caller translation units |
| C06 formatting/warnings | Require warning-clean build and exact `HH:MM` output | a2/a5 `snprintf`; a4/a8 unpadded output | Run verifier 06 | Strict compile plus boundary rendering |
| C07 canonical semantics | Check modulo-day construction, signed arithmetic, and normalized equality | a2 retry has latent negative-day error | Run verifier 07 | Public black-box probes only |
| C08 official terminal | Authenticate and execute all pinned official tests | Only terminal correctness oracle | Run verifier 08 | Mandatory for success |
| C09 repair transition | Compare before/after aggregate receipts | 0/4 Clock feedback recoveries | Run verifier 09 on two summaries | Diagnostic only; not reward-enabled |

## Layout

```text
clock_verifiers_v2/
├── Instruction/       # frozen behavioral/reward contracts
├── Implementation/    # implementation reports and limitations
├── verifiers/         # executable policies and aggregate runner
└── validation/        # controlled-mutant harness and receipts/report
```

## Reward contract

- C01-C07 are granular shaping signals; none proves task correctness alone.
- C08 is mandatory. `terminal_success` is true only when C08 passes.
- `reward_ready` is true only when all C01-C08 pass.
- Candidate failure is `-1`; verified success is `+1`; evaluator/asset/tool failure is `INVALID` and has no numeric reward.
- C09 never emits candidate reward. It prevents a trajectory-analysis heuristic from silently entering the training objective.
- Kernels and categories overlap by design and must not be summed as independent failure counts.

## Run

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/pinned/clock \
  --output-dir /new/empty/output
```

Every category may also be run independently with the same two arguments. See each instruction report for its pass boundary.

## Direct facts and boundaries

- The current official Exercism Clock API and tests are semantically equivalent to the pinned benchmark assets; only pinned hashes are accepted at runtime.
- Probes use public behavior and compiler/linker results, not candidate private-member spelling.
- A failed shaping category locates a boundary; it does not prove one unique root cause.
- Live reward-worker wiring, throughput, and calibration against model-generated distributions require a separate integration run.

## Conclusion

The structure keeps contracts, implementation decisions, executable code, and validation evidence separate. The remaining production risk is reward calibration, so the next check after deterministic mutation validation is a shadow run on real GRPO trajectories with C08 held as the terminal gate.
