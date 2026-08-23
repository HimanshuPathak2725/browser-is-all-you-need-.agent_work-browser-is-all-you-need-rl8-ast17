# Policy G03 — API Caller and Link Contract

## Purpose

Run a task-owned caller probe that compiles and links the public API exactly as the pinned task requires.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G03-A… | Does each trusted API/link probe succeed? | Expected exit code | Candidate violates the supplied API/link contract | Probe or manifest evidence is invalid |

## Shared method

The framework never supplies names, types, namespaces, or behavior. Those remain task-owned probe data in the trusted manifest.

## Aggregation

Declared probes are equal `+1/-1` kernels. This policy is structural and cannot establish semantic correctness.

## Execution

`python verifier_03_api_link.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
