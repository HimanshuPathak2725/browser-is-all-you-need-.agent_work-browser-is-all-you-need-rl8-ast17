# Policy G10 — Lifecycle, State Isolation, and Repeatability

## Purpose

Run authenticated task-owned probes for state transitions, fresh-instance isolation, reset behavior, repeated identical inputs, and deterministic or contract-bounded repeated execution.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G10-A… | Does each declared lifecycle or repeatability probe succeed? | Expected exit code | Candidate violates the task-owned state or repeatability contract | Probe, command schema, or verifier dependency is invalid |

## Shared method

The manifest defines only behavior supported by the pinned task contract. It may supply transition sequences, fresh-object comparisons, reset checks, or repeated executions, but it must not require one private state representation or demand determinism from a contract that permits randomness.

Every G10 command must declare `characteristic_id: C7`, a unique lowercase-hyphenated `probe_id`, and one of these `evidence_kind` values: `lifecycle-transition`, `state-isolation`, `reset-behavior`, or `repeatability`. Missing or mismatched metadata makes the policy `INVALID` before the command runs.

## Aggregation

Each independently declared lifecycle or repeatability command is an equal binary kernel. G10 is shaping evidence and cannot replace authenticated G04 terminal success.

## Execution

`python verifier_10_lifecycle_state_repeatability.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
