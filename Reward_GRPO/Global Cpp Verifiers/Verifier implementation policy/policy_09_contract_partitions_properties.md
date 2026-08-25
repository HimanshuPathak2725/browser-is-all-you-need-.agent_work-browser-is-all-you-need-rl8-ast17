# Policy G09 — Contract Partitions and Metamorphic Properties

## Purpose

Run authenticated task-owned probes for semantic edge partitions, relational behavior, generated cases, independent oracles, and metamorphic properties beyond the official examples.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G09-A… | Does each declared semantic partition or property hold? | Expected exit code | Candidate violates the task-owned semantic probe | Probe, expected value, command schema, or verifier dependency is invalid |

## Shared method

The framework supplies process isolation, evidence authentication, receipts, and binary kernel interpretation. Every name, input partition, property, and expected value remains in the trusted task manifest or its protected probe assets; the framework never invents cross-task semantics.

Every G09 command must declare `characteristic_id: C6`, a unique lowercase-hyphenated `probe_id`, and one of these `evidence_kind` values: `edge-partition`, `relational-property`, `independent-oracle`, or `metamorphic-property`. Missing or mismatched metadata makes the policy `INVALID` before the command runs.

## Aggregation

Each independently declared partition or property command is an equal binary kernel. G09 is shaping evidence and cannot replace authenticated G04 terminal success.

## Execution

`python verifier_09_contract_partitions_properties.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
