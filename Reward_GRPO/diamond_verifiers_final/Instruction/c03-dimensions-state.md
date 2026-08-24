# DMF-C03 instruction: dimensions and state

## Contract

For every input from A through Z, `rows(letter)` must return a square of side `2 * (letter - 'A') + 1`. Repeated and interleaved calls must be deterministic and must not leak or retain mutable result state.

| Kernel | Pass condition |
| --- | --- |
| C03-A | All 26 outputs contain the expected number of rows and exact row width |
| C03-B | Repeated, interleaved, ascending, and saved-result calls remain identical |

This policy isolates shape and state failures without requiring exact row bytes; exact placement is owned by C04 and C05.
