# C02 instruction: dependency and header completeness

## Observed failure

Trial a4 repaired padding with `std::setw` and `std::setfill` but omitted `<iomanip>`. The failure was deterministic and directly identified by GCC.

## Contract

`clock.h` must compile when included first in an otherwise empty translation unit. The implementation must explicitly provide every standard-library declaration it uses and must not depend on test include order.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C02-A | Header included first compiles |
| C02-B | Implementation compiles with only its own includes and strict flags |
| C02-C | Stream-format caller links and renders `08:03` |

The verifier uses compilation rather than textual include matching, so equivalent legal dependency strategies remain valid.
