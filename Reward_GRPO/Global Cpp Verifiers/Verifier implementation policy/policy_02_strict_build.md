# Policy G02 — Strict Build

## Purpose

Run pinned warning-clean build commands that detect compile, template, include, and link defects without assuming task behavior.

| Kernel | Question | `+1` | `-1` | `INVALID` |
|---|---|---|---|---|
| G02-A… | Does each trusted strict-build command succeed? | Expected exit code | Candidate command fails or times out | Command schema or verifier dependency is invalid |

## Shared method

The manifest provides safe argument-list commands, expected exit codes, and bounded timeouts. Logs are written outside candidate source and source digest remains recorded in the receipt.

## Aggregation

Every declared command is an equal binary kernel. The policy passes only when its kernel sum equals its maximum sum.

## Execution

`python verifier_02_strict_build.py --candidate-dir TASK --manifest MANIFEST --expected-manifest-sha256 DIGEST --output-dir OUT`
