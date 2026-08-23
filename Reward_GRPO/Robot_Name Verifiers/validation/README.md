# Robot Name validation evidence

This directory preserves the real-output-first Strange audit run on 2026-08-23.

| Artifact | Purpose |
|---|---|
| `failure_gap_manifest.json` | Pins the Midband run/checkpoint, GCS evaluation root, eight candidate snapshots, source receipt hashes, and verifier bytes |
| `cases/` | Exact Robot Name source states for all eight evaluation turns |
| `fixed/instructions.md` | Exact task instructions required by the pinned verifier contract, SHA-256 `b2750750…cc68b2f7` |
| `failure_gap_replay_receipt.json` | Five-policy replay over all eight authentic candidate states |
| `control_validation_receipt.json` | Positive, mutation, evaluator-fault, source-immutability, and repeatability evidence |
| `structure_validation_receipt.json` | Policy/verifier pairing, AST, comment, hash, fixed-asset, and kernel-count evidence |

The replay uses the full-pack decision rule: `INVALID` if any policy is invalid, otherwise FAIL if any policy fails, otherwise PASS. E03 remains the authenticated official-suite policy, but it is not sufficient alone for this stochastic task.

Run the three validators only in the pinned offline image with the repository mounted read-only, an empty writable output directory, and `STRANGE_ISOLATED_REPLAY=1` for the gap/control runners. The entry points are `run_structure_validation.py`, `run_failure_gap_audit.py`, and `run_control_validation.py`; deterministic staging and result normalization are in `validation_common.py`.

The local immutable fixture is `local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z/benchmark-output-shard-1/cpp/exercises/practice/robot-name`. Its official tests and metadata match the contract; its older `.docs/instructions.md` does not, so `fixed/instructions.md` is overlaid during replay and its distinct hash is explicitly authenticated.
