# CLF-C05 policy: canonical time properties

## Contract

Construction, addition, subtraction, equality, and inequality must implement a date-independent modulo-1,440-minute clock. Mutations return the same object by reference, signed day crossings normalize canonically, and equality represents exact normalized time.

| Kernel | Pass condition |
| --- | --- |
| C05-A | 289 signed hour/minute combinations equal an independent modulo-day oracle |
| C05-B | 306 plus/minus combinations match the oracle, preserve identity, and reverse correctly |
| C05-C | Equality laws plus explicit adjacent-hour/minute ground truths and state isolation pass |

All three probes compile with UBSan and abort on observed undefined behavior. Tested values avoid overflow in the pinned reference while spanning large signed inputs and multiple-day deltas.

## Implementation rationale

`verifier_05_time_properties.py` unifies original E02/E04 and v2 C07 into three high-density property executables. The construction grid evaluates 289 combinations; arithmetic evaluates 306 plus/minus combinations; relation checks cover algebraic laws and explicit true/false ground truths.

The probes use independent `long long` modulo-day oracles and compile with `-fsanitize=undefined -fno-sanitize-recover=undefined`. Mutation testing exposed that algebraic consistency alone missed a consistently wrong equality pair, so adjacent-minute/hour and normalized-equivalence assertions were added before the final campaign.
