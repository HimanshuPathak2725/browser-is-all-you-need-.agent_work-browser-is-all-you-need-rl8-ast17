# CLF-C05 instruction: canonical time properties

## Contract

Construction, addition, subtraction, equality, and inequality must implement a date-independent modulo-1,440-minute clock. Mutations return the same object by reference, signed day crossings normalize canonically, and equality represents exact normalized time.

| Kernel | Pass condition |
| --- | --- |
| C05-A | 289 signed hour/minute combinations equal an independent modulo-day oracle |
| C05-B | 306 plus/minus combinations match the oracle, preserve identity, and reverse correctly |
| C05-C | Equality laws plus explicit adjacent-hour/minute ground truths and state isolation pass |

All three probes compile with UBSan and abort on observed undefined behavior. Tested values avoid overflow in the pinned reference while spanning large signed inputs and multiple-day deltas.
