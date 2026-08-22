# CLF-C05 implementation report

`verifier_05_time_properties.py` unifies original E02/E04 and v2 C07 into three high-density property executables. The construction grid evaluates 289 combinations; arithmetic evaluates 306 plus/minus combinations; relation checks cover algebraic laws and explicit true/false ground truths.

The probes use independent `long long` modulo-day oracles and compile with `-fsanitize=undefined -fno-sanitize-recover=undefined`. Mutation testing exposed that algebraic consistency alone missed a consistently wrong equality pair, so adjacent-minute/hour and normalized-equivalence assertions were added before the final campaign.
