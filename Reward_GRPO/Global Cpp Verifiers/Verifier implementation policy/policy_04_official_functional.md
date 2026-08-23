# Policy G04 — Authenticated Official Functional Behavior

## Purpose

Run the pinned official suite as the authoritative terminal semantic gate for any task.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G04-A… | Does the trusted official suite pass? | Expected exit code | Candidate fails functional test or times out | Runner, command schema, or evidence is invalid |

## Shared method

The framework authenticates protected assets before launching the task-owned official command. It does not replace task semantics with generic assertions.

## Aggregation

All official commands are equal binary kernels. At least one G04 command is mandatory for any claimed terminal success.

## Execution

`python verifier_04_official_functional.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
