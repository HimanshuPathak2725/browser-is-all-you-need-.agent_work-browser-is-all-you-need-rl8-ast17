# DNF-C06 policy: authenticated official terminal

Authenticate the pinned instructions, metadata, reference files, build files, Catch2 harness, and D&D Character test file. Compile the complete official suite in C++17 with strict warnings, enable all Exercism tests, and execute it.

Terminal success requires the exact successful summary for 24 assertions in 18 test cases. A candidate-caused build or test failure is `FAIL`; protected-asset, compiler, execution, receipt, or source-integrity failure is `INVALID`.

This policy is the official compatibility gate. Strict reward readiness additionally requires DNF-C01 through DNF-C05 because the official random tests observe range and hit-point consistency but not the required dice distribution or six-roll independence.

## Implementation rationale

The terminal policy uses the same pinned Aider Polyglot task assets as the other final packages, but compiles with strict warnings and requires the exact complete-suite count. Authentication happens before candidate compilation, so changed tests or reference assets become `INVALID`.

Official success is reported separately from strict success. This preserves benchmark comparability while preventing the official suite's shallow random checks from granting full reward to statistically incorrect generators.
