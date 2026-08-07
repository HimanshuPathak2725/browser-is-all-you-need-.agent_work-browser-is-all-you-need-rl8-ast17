# Public-PR model evaluation diagnosis

These tasks are public-patch diagnostics and are not clean generalization evidence.
Executable oracle results are authoritative; upstream patch similarity is diagnostic.

| Task | Pass@1 | Pass@2 | Final failure class | Exact upstream patch |
| --- | ---: | ---: | --- | ---: |
| `fmtlib-fmt-large-time-point-overflow-v2` | False | False | `no_production_change` | False |

Each task directory contains the candidate patch, evaluator-only upstream patch,
candidate-to-reference diff, failed-command log tail, and machine-readable receipt
for every attempted response.
