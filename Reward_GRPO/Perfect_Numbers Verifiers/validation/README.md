# Perfect Numbers validation evidence

This directory preserves the real-output-first Strange audit run on 2026-08-23.

| Artifact | Purpose |
|---|---|
| `failure_gap_manifest.json` | Pins the Midband run/checkpoint, GCS evaluation root, exact candidate and source-receipt hashes, contract, and current verifier bytes |
| `cases/` | Six replayable source snapshots: Trial 1 before/after repair, Trial 2 and Trial 3 passes, and Trial 4 before/after regression |
| `fixed/instructions.md` | Pristine pinned verifier-contract instructions, SHA-256 `8db797c5…b92b1cb` |
| `fixed/source_overlay_instructions.md` | Exact Midband task overlay, SHA-256 `6f06b35f…d4b1506` |
| `failure_gap_replay_receipt.json` | E01–E03 replay over six sources plus E04 replay over two authenticated trajectories |
| `control_validation_receipt.json` | Positive, focused mutation, evaluator-fault, source-immutability, and repeatability results |
| `structure_validation_receipt.json` | Policy/verifier pairing, AST, source-comment, hash, and kernel-count evidence |

Run the validators only in the pinned offline image with the repository mounted read-only, an empty writable output directory, and `STRANGE_ISOLATED_REPLAY=1` for the gap/control runners. The executed entry points are `run_structure_validation.py`, `run_failure_gap_audit.py`, and `run_control_validation.py`; shared deterministic staging is in `validation_common.py`.

The fixture is `local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z/benchmark-output-shard-1/cpp/exercises/practice/perfect-numbers`. The verifier contract uses the pristine instruction hash; the manifest separately records the richer Midband prompt overlay so the two authenticated roles are never mixed.
