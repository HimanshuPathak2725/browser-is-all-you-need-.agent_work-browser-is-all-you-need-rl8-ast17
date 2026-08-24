# Policy G06 — Non-Directive Trajectory and Feedback Boundary

## Purpose

Audit optional two-turn evidence while keeping verifier telemetry outside the model context and separate from semantic success.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G06-A | Is trajectory telemetry well-formed? | Ordered receipts have valid nonnegative counters | Not applicable | Schema or receipt fields are invalid |
| G06-B | Was retry feedback preserved? | Generated and delivered feedback bytes match | Feedback bytes differ | Required feedback evidence is malformed |

## Shared method

Context exhaustion and model-error counters are recorded as telemetry only. They never negate a candidate that passed G04. The verifier neither reads hidden reasoning nor writes instructions into a model request; any retry feedback is task-runner output, not verifier-authored guidance.

## Aggregation

G06 is excluded when no authenticated trajectory exists. When present, its kernels use the same equal `+1/-1/INVALID` model, but it is an audit policy and not a terminal semantic gate.

## Execution

`python verifier_06_trajectory_boundary.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
