# CLF-C06 instruction: authenticated official terminal behavior

## Contract

The pinned official tests, metadata, reference files, Catch2 dependency, and build assets must match their SHA-256 values. All selected tests must compile, link, execute, exit zero, and report that all tests passed.

| Kernel | Pass condition |
| --- | --- |
| C06-A | Every protected task asset authenticates |
| C06-B | The full suite builds with `EXERCISM_RUN_ALL_TESTS` |
| C06-C | The executable exits zero with the all-tests-passed marker |

C06 alone defines correctness in `official` acceptance mode. C01-C05 remain valuable diagnostics but cannot override authenticated official success in that mode.
