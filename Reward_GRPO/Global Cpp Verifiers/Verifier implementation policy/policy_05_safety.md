# Policy G05 — Applicable Safety and Undefined-Behavior Checks

## Purpose

Run task-owned sanitizer or safety stress probes when the contract has memory, ownership, concurrency, or bounds behavior.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G05-A… | Does each applicable trusted safety command succeed? | Expected exit code | Candidate violates the safety probe or times out | Tooling or manifest evidence is invalid |

## Shared method

Safety is optional by task. A task with no safety-relevant contract omits G05 commands rather than receiving invented constraints.

## Aggregation

Applicable commands are equal binary kernels. An omitted safety policy is excluded with an explicit manifest reason at orchestration time.

## Execution

`python verifier_05_safety.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
