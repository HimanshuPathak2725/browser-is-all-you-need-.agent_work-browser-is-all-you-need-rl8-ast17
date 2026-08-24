# Reward_GRPO verifier validation index

This index records the real-output-first Strange validation completed on 2026-08-23 for the eleven requested Midband-RL-v2 topics. Every topic has a three-step report, a failure-gap manifest, replay/control/structure receipts, a validation README, and a setup status. Across the list, 11 manifests and 37 receipts parse as JSON and all report/diff integrity checks pass.

All eleven verifier layers are `READY`. All eleven live GRPO integrations remain `CONDITIONALLY READY` because verifier correctness does not by itself prove that the training reward adapter executes every required kernel, preserves terminal gates, supplies trusted bundles, and discards `INVALID` samples.

| Topic | Midband pass@1 → by turn 2 | Verifier result | Evidence-backed package decision | Required live terminal rule | Report SHA-256 |
|---|---:|---|---|---|---|
| Allergies | `3/4 → 4/4` | READY | Relax E02 to official-compatible string-literal APIs; add only authenticated E05 missing-include repair class | E06 terminal; E05 only for trusted two-turn bundles | `0b28d3ff…fedad` |
| Circular Buffer | `1/4 → 2/4` | READY | Correct fixed contract to bind both editable files; keep five policies | E03 terminal | `06fb2fff…6034` |
| Clock | `2/4 → 2/4` | READY | Existing five policies sufficient; no change | E03 terminal | `4ca546c0…ba26` |
| Complex Numbers | `0/4 → 1/4` | READY | Remove undocumented exact stream-text restriction from E04; preserve semantic checks | E03 terminal | `abf70c88…d831` |
| Diamond | `0/4 → 0/4` | READY | Existing ten policies cover all eight failed states; add nothing | E05+E06 terminal; E07/E08 trusted bundles | `05a744b8…a7d6` |
| Grade School | `2/4 → 2/4` | READY | Existing ten policies sufficient; add nothing | E05+E06 terminal; E07/E08 trusted bundles | `c6725c2d…e401` |
| Parallel Letter Frequency | `2/4 → 2/4` | READY | Existing five policies sufficient; add nothing | E03 terminal | `d2d7a1a2…f236` |
| Perfect Numbers | `2/4 → 3/4` | READY | Existing four policies cover every observed state; add nothing | Combined E01–E03 terminal; E04 trusted trajectory only | `5f67aeaf…a30e` |
| Robot Name | `0/4 → 1/4` | READY | Keep five policies and require full-pack decision; official suite alone can be stochastic | All E01–E05 terminal | `549a3d86…87d` |
| Spiral Matrix | `2/4 → 2/4` | READY | Existing five policies cover compile and unsigned size-2 failures; add nothing | All E01–E05 terminal | `320da8e7…586b` |
| Sublist | `4/4 → 4/4` | READY | Existing ten policies accept all real/alternate valid forms; add nothing | E05+E06 semantic terminal; E07/E08 trusted bundles | `46aa4c4a…89cb` |

## Common reward rules

- Execute verifier kernels in the backend; do not paste policy prose into model prompts.
- Preserve independent shaped signals instead of reducing the package to one sequential first-failure score.
- Require each topic's stated terminal gate before assigning full reward.
- Treat compiler, fixed-asset, parser, toolchain, or trusted-bundle faults as `INVALID`; rerun them and never charge them to the model.
- Keep trajectory/harness policies bundle-bound and keep sanitizer/cross-compiler policies on their intended periodic schedule unless rollout capacity explicitly supports them.
- Do not add another policy without an authenticated model miss and an alternate-valid control proving the new boundary does not over-restrict.
- Infrastructure, training, SkyPilot, checkpoint, and launch files were outside this validation change boundary.

## Report locations

| Topic | Detailed report | Setup contract |
|---|---|---|
| Allergies | `Reward_GRPO/Allergies Verifiers/VALIDATION_REPORT.md` | `strange/strange/allergies-setup.md` |
| Circular Buffer | `Reward_GRPO/Circular_Buffer Verifiers/VALIDATION_REPORT.md` | `strange/strange/circular-buffer-setup.md` |
| Clock | `Reward_GRPO/Clock Verifiers/VALIDATION_REPORT.md` | `strange/strange/clock-setup.md` |
| Complex Numbers | `Reward_GRPO/Complex_Numbers Verifiers/VALIDATION_REPORT.md` | `strange/strange/complex-numbers-setup.md` |
| Diamond | `Reward_GRPO/Diamond Verifiers/VALIDATION_REPORT.md` | `strange/strange/diamond-setup.md` |
| Grade School | `Reward_GRPO/Grade_School Verifiers/VALIDATION_REPORT.md` | `strange/strange/grade-school-setup.md` |
| Parallel Letter Frequency | `Reward_GRPO/Parallel_Letter_Frequency Verifiers/VALIDATION_REPORT.md` | `strange/strange/parallel-letter-frequency-setup.md` |
| Perfect Numbers | `Reward_GRPO/Perfect_Numbers Verifiers/VALIDATION_REPORT.md` | `strange/strange/perfect-numbers-setup.md` |
| Robot Name | `Reward_GRPO/Robot_Name Verifiers/VALIDATION_REPORT.md` | `strange/strange/robot-name-setup.md` |
| Spiral Matrix | `Reward_GRPO/Spiral_Matrix Verifiers/VALIDATION_REPORT.md` | `strange/strange/spiral-matrix-setup.md` |
| Sublist | `Reward_GRPO/Sublist Verifiers/VALIDATION_REPORT.md` | `strange/strange/sublist-setup.md` |
