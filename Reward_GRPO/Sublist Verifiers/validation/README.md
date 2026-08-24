# Sublist validation evidence

This directory preserves the real-output-first Strange audit completed on 2026-08-23.

| Artifact | Purpose |
|---|---|
| `failure_gap_manifest.json` | Pins the Midband run/checkpoint, GCS root, four authentic final candidates, source evidence hashes, fixed contract, and verifier bytes |
| `cases/` | Exact final `sublist.h` and `sublist.cpp` bytes from all four Midband trials |
| `fixed/instructions.md` | Hash-pinned contract overlay, SHA-256 `87fec6e1…a81288` |
| `failure_gap_replay_receipt.json` | E01–E06/E09 replay over all four authentic candidates |
| `control_validation_receipt.json` | Alternate-valid, semantic-mutant, evaluator-fault, immutability, and repeatability evidence |
| `portability_host_receipt.json` | E10 replay under host Clang 18.1.3 |
| `portability_container_receipt.json` | E10 replay in immutable image `glm47-verifier-toolchain-probe@sha256:d641bb62…170d4` with Clang 18.1.8 |
| `structure_validation_receipt.json` | Ten policy/verifier pairs, AST/comment checks, runtime hash, and 46-kernel inventory |

The source decision rule is `INVALID` if any required kernel has evaluator-invalid evidence, otherwise FAIL if a required terminal policy fails, otherwise PASS. E05 is the authenticated official-suite layer and E06 is the independent semantic layer. E07 and E08 require trusted bundles and are intentionally not synthesized from source-only eval folders.

Run the structure, failure-gap, control, and portability entry points only with new empty output directories. The GCC campaigns require `STRANGE_ISOLATED_REPLAY=1`, the pinned offline GCC 13.3.0 image, a read-only repository mount, disabled networking, and a separate writable output mount. Portability is repeated under exact host Clang 18.1.3 and the pinned offline Clang toolchain image.

The local fixed fixture is `local-results/job22-iter5-fixed26-v5-pathfix-20260814T071410Z/benchmark-output-shard-1/cpp/exercises/practice/sublist`. Its bundled instruction copy predates the contract overlay, so every runner overlays and authenticates `fixed/instructions.md` before scoring.
