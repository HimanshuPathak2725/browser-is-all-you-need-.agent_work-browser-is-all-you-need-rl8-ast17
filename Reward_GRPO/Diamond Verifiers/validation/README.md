# Diamond validation evidence

This directory preserves the exact Midband-RL-v2 Diamond candidates and the current-verifier audit used by `../VALIDATION_REPORT.md`.

Run the three stages in the pinned validation image from the repository root:

```bash
python3 'Reward_GRPO/Diamond Verifiers/validation/run_failure_gap_audit.py' --output /tmp/diamond-gap.json
python3 'Reward_GRPO/Diamond Verifiers/validation/run_control_validation.py' --output /tmp/diamond-controls.json
python3 'Reward_GRPO/Diamond Verifiers/validation/run_structure_validation.py' --output /tmp/diamond-structure.json
```

The saved receipts are immutable evidence from GCC 13.3.0 in the pinned offline image. E07 and E08 require authenticated two-turn/Aider bundles, and E10 requires the separately pinned Clang 18.1.3 environment; source-only replay does not claim those inputs existed.

| Artifact | Purpose |
|---|---|
| `failure_gap_manifest.json` | Pins source run, checkpoint, candidates, hashes, and expected classifications |
| `cases/` | Exact model-produced `diamond.h/.cpp` snapshots |
| `fixed/instructions.md` | Pinned canonical task instructions |
| `failure_gap_replay_receipt.json` | Existing-verifier classification of all real outputs |
| `control_validation_receipt.json` | Positive, mutation, invalid, immutability, and repeatability evidence |
| `structure_validation_receipt.json` | Policy/verifier pairing and kernel inventory |
