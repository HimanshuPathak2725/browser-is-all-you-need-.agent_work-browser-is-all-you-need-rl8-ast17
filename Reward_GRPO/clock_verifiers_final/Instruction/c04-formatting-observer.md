# CLF-C04 instruction: formatting and observer stability

## Contract

String conversion must return exactly `HH:MM` for canonical and normalized signed inputs. It must remain stable across repeated calls on const objects and use five ASCII characters with a colon at index two.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Every canonical minute from `00:00` through `23:59` renders exactly |
| C04-B | Seventeen large, negative, and whole-day inputs match an independent oracle |
| C04-C | Five const clocks remain unchanged over 100 repeated conversions each |

The expected strings are computed independently in probe code; no implementation-specific formatting library is required.
