# Policy G08 — Header, Dependency, and ODR Integrity

## Purpose

Run trusted structural probes for self-contained public headers, repeated inclusion, protected-dependency isolation, and multi-translation-unit one-definition-rule behavior.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G08-A… | Does each applicable structural integration probe succeed? | Expected exit code | Candidate violates the declared header, dependency, or ODR contract | Probe, command schema, or verifier dependency is invalid |

## Shared method

The authenticated task manifest owns the candidate header list and probe commands. A typical manifest supplies separate self-contained-header, double-include, protected-include, and two-translation-unit link commands. The global verifier does not require a particular include-guard spelling, file layout, or private representation.

Every G08 command must declare `characteristic_id: C4`, a unique lowercase-hyphenated `probe_id`, and one of these `evidence_kind` values: `header-self-contained`, `repeated-include`, `protected-dependency`, or `multi-tu-odr`. Missing or mismatched metadata makes the policy `INVALID` before the command runs.

## Aggregation

Applicable commands are equal binary kernels. A task with no candidate header excludes G08 rather than receiving an invented structural requirement.

## Execution

`python verifier_08_header_dependency_odr.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
