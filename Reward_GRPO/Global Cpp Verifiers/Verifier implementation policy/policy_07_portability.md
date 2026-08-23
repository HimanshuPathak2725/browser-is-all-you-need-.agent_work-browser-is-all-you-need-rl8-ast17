# Policy G07 — Applicable Toolchain Portability

## Purpose

Run pinned alternate-toolchain checks without requiring a task to adopt any particular implementation strategy.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G07-A… | Does each applicable portability command succeed? | Expected exit code | Candidate is nonportable under the declared toolchain | Toolchain or manifest evidence is invalid |

## Shared method

The task manifest chooses the compiler and test command. The global framework only preserves process isolation, receipts, and binary interpretation.

## Aggregation

Applicable commands are equal binary kernels. Tasks without an alternate supported compiler exclude G07 rather than failing it.

## Execution

`python verifier_07_portability.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
