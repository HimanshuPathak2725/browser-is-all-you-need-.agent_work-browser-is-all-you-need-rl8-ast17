# Policy G01 — Candidate and Protected-Asset Boundary

## Purpose

Authenticate the candidate directory, its editable-file digest, and pinned protected assets before any generic verifier result is emitted.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G01-A | Is the candidate boundary authentic? | All declared candidate files and protected hashes are valid | Not applicable | Missing, unsafe, or hash-drifting evidence |

## Shared method

The trusted manifest is supplied outside the candidate directory with its expected SHA-256. The verifier rejects symlinks, unsafe paths, output inside source, and nonempty output directories.

## Aggregation

G01 is a prerequisite integrity policy. Its valid kernel returns `+1`; any boundary or infrastructure defect is `INVALID` and is never model failure.

## Execution

`python verifier_01_candidate_boundary.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
