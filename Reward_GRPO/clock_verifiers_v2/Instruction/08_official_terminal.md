# C08 instruction: authenticated official terminal behavior

## Purpose

Category probes are incomplete by construction. This policy is the only terminal correctness oracle: it authenticates and runs every selected pinned official Clock test.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C08-A | All protected tests, metadata, reference, and build assets match pinned SHA-256 values |
| C08-B | Official test executable compiles and links with all tests enabled |
| C08-C | Executable exits zero and reports all tests passed |

Any asset/tool fault is `INVALID`. Candidate compile, link, runtime, or assertion failure is `-1`. Terminal success requires C08 3/3 regardless of shaping scores.
