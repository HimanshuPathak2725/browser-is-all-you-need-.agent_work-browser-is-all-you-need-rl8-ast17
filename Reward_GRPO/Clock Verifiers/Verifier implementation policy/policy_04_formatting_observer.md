# CLF-C04 policy: formatting and observer stability

## Contract

String conversion must return exactly `HH:MM` for canonical and normalized signed inputs. It must remain stable across repeated calls on const objects and use five ASCII characters with a colon at index two.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Every canonical minute from `00:00` through `23:59` renders exactly |
| C04-B | Seventeen large, negative, and whole-day inputs match an independent oracle |
| C04-C | Five const clocks remain unchanged over 100 repeated conversions each |

The expected strings are computed independently in probe code; no implementation-specific formatting library is required.

## Implementation rationale

`verifier_04_formatting_observer.py` replaces a few hand-picked formatting assertions with an exhaustive 1,440-minute canonical sweep, a 17-input signed boundary table, and 500 repeated const observations. Expected output is constructed directly from normalized integers rather than by reusing candidate logic.

This is broader than original E02/E05 and v2 C06 while remaining deterministic and inexpensive. Formatting failures may overlap C05 or C06 when incorrect normalization changes rendered output.
