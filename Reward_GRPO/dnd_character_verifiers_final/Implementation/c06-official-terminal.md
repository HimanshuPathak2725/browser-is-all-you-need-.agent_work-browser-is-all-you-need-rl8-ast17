# Implementing DNF-C06

The terminal policy uses the same pinned Aider Polyglot task assets as the other final packages, but compiles with strict warnings and requires the exact complete-suite count. Authentication happens before candidate compilation, so changed tests or reference assets become `INVALID`.

Official success is reported separately from strict success. This preserves benchmark comparability while preventing the official suite's shallow random checks from granting full reward to statistically incorrect generators.
