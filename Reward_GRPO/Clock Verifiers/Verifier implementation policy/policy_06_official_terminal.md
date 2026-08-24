# CLF-C06 policy: authenticated official terminal behavior

## Contract

The pinned official tests, metadata, reference files, Catch2 dependency, and build assets must match their SHA-256 values. All selected tests must compile, link, execute, exit zero, and report that all tests passed.

| Kernel | Pass condition |
| --- | --- |
| C06-A | Every protected task asset authenticates |
| C06-B | The full suite builds with `EXERCISM_RUN_ALL_TESTS` |
| C06-C | The executable exits zero with the all-tests-passed marker |

C06 alone defines correctness in `official` acceptance mode. C01-C05 remain valuable diagnostics but cannot override authenticated official success in that mode.

## Implementation rationale

`verifier_06_official_terminal.py` preserves the shared authenticated official executor used by original CL-E03 and v2 CL2-C08. This is intentionally not replaced by selected property checks: a targeted `(201, 3001)` mutant proved that partial policies can all pass while an official case fails.

Protected-asset or compiler faults produce `INVALID`; candidate compile, link, assertion, or runtime failures produce `FAIL`. The aggregate exposes C06 separately as `official_success` and never derives it from shaping scores.
