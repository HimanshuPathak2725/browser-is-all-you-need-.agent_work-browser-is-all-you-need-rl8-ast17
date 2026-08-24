# Spiral Matrix validation evidence

This directory preserves the real-output-first Strange audit run on 2026-08-23.

| Artifact | Purpose |
|---|---|
| `failure_gap_manifest.json` | Pins the Midband run/checkpoint, GCS root, six evaluated candidate states, source hashes, and verifier bytes |
| `cases/` | Exact or chat-reconstructed source states for every evaluated turn |
| `fixed/instructions.md` | Exact Midband task instructions required by the verifier contract, SHA-256 `9d5dff44…c92bfb3` |
| `failure_gap_replay_receipt.json` | Five-policy replay over all six evaluated source states |
| `control_validation_receipt.json` | Positive, focused mutation, evaluator-fault, source-immutability, and repeatability evidence |
| `structure_validation_receipt.json` | Policy/verifier pairing, AST, comment, hash, fixed-asset, and kernel-count evidence |

The replay uses the full-pack decision rule: `INVALID` if any policy is invalid, otherwise FAIL if any policy fails, otherwise PASS. E03 is the authenticated official-suite policy; E04 and E05 preserve the more specific size-2 and sanitizer reward signals.

Run the validators only in the pinned offline image with the repository mounted read-only, an empty writable output directory, and `STRANGE_ISOLATED_REPLAY=1` for gap/control runners. Entry points are `run_structure_validation.py`, `run_failure_gap_audit.py`, and `run_control_validation.py`; shared staging is in `validation_common.py`.

The fixture is `local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z/benchmark-output-shard-1/cpp/exercises/practice/spiral-matrix`. Its official tests and metadata match the contract; its older instruction copy does not, so `fixed/instructions.md` is explicitly overlaid and authenticated during replay.
