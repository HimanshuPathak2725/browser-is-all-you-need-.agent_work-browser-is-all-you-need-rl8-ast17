# C08 implementation report: official terminal behavior

`verifier_08_official_terminal.py` delegates to the shared authenticated official-suite executor. It hash-checks every protected Clock asset, compiles all tests with `EXERCISM_RUN_ALL_TESTS`, and requires Catch2's successful terminal result.

The reference passed 3/3. A targeted case-specific mutant passed C01-C07 and failed only C08, directly proving why partial policies cannot grant task success. All eight controlled source mutants were rejected by C08.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C08-A | Pinned SHA-256 authentication | Fixed asset hash map |
| C08-B | Full official compile/link | Command log and executable hash |
| C08-C | Exit zero plus all-tests-passed marker | Complete stdout/stderr |

Tampered tests and a missing compiler produced `INVALID`, not candidate `-1`. Live worker integration remains unverified.
