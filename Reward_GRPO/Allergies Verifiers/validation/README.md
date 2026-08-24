# Allergies failure-gap validation

This directory preserves the exact Midband-RL-v2 Allergies source snapshots and the deterministic runners used by `VALIDATION_REPORT.md`. Perfectly formed sources are positive controls only. Real model outputs establish failure gaps; targeted mutations check discrimination; evaluator faults must produce `INVALID`.

## Saved evidence

| Artifact | Result | SHA-256 |
|---|---|---|
| `structure_validation_receipt.json` | 6 policies, 6 verifiers, 11 candidate kernels, 5 trajectory kernels; PASS | `1f8ced968e30921dd107e1a980b6d4b22ae06c702f02dc86322ac10f272add18` |
| `failure_gap_replay_receipt.json` | 4 agreement-passes, 1 agreement-fail, 0 missed failures, 0 restrictions | `ff7c6cb7107cc2dd406c995163603d0a442372849706deb8fb22147e115d6c08` |
| `control_validation_receipt.json` | 3/3 valid implementations accepted; 4 targeted defects and semantic adversary rejected as expected; 2 evaluator faults INVALID | `17d707c86595c86b31ba479e78cce2400d3364e6356c77b3948c11d0f375e824` |
| `trajectory_validation_receipt.json` | Real repair +5/5; baseline INVALID; evidence-fault and applicability controls match | `8d867fc47b186762ec827ed25994d028fc0d59dcd32a49496160621bcfa2f2a7` |

## Execution boundary

All executable validation was run with network disabled, a read-only repository mount, all Linux capabilities dropped, an ephemeral `/tmp`, and this immutable image:

```text
glm47-reward-grpo-bank-account@sha256:e4d1090d07cab73e5c4137637beccebe1dac0f6aa440e7d4cbfc466c4f226932
```

The image reports GCC `13.3.0`. Each runner requires an absent or empty output directory. The repository should be mounted read-only and only a dedicated temporary result directory should be writable.

## Step 1: Structure

```bash
python3 "Reward_GRPO/Allergies Verifiers/validation/run_structure_validation.py" \
  --output-dir /validation-output/structure
```

## Step 2: Real-output replay

```bash
STRANGE_ISOLATED_REPLAY=1 \
python3 "Reward_GRPO/Allergies Verifiers/validation/run_failure_gap_audit.py" \
  --output-dir /validation-output/failure-gap \
  --workers 4
```

## Step 3: Positive, alternate-valid, defect, and evaluator-fault controls

```bash
STRANGE_ISOLATED_REPLAY=1 \
python3 "Reward_GRPO/Allergies Verifiers/validation/run_control_validation.py" \
  --output-dir /validation-output/controls
```

## Step 4: Two-turn repair controls

```bash
STRANGE_ISOLATED_REPLAY=1 \
python3 "Reward_GRPO/Allergies Verifiers/validation/run_trajectory_validation.py" \
  --output-dir /validation-output/trajectory
```

Compare normalized decisions and source hashes when repeating a run. Receipt timestamps, temporary absolute paths, command durations, and receipt hashes that transitively include those fields are not expected to remain byte-identical.
