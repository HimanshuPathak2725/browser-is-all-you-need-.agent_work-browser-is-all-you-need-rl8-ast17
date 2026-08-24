# DMF-C03 policy: dimensions and state

## Contract

For every input from A through Z, `rows(letter)` must return a square of side `2 * (letter - 'A') + 1`. Repeated and interleaved calls must be deterministic and must not leak or retain mutable result state.

| Kernel | Pass condition |
| --- | --- |
| C03-A | All 26 outputs contain the expected number of rows and exact row width |
| C03-B | Repeated, interleaved, ascending, and saved-result calls remain identical |

This policy isolates shape and state failures without requiring exact row bytes; exact placement is owned by C04 and C05.

## Implementation rationale

`verifier_03_dimensions_state.py` checks all 26 input sizes and every row width, then exercises saved, repeated, and interleaved calls. This targets the dominant iter-19 failure family: compile-clean implementations whose row count, width, or retained state is wrong.

The probes use only the public API and independent side-length arithmetic. Three of the four observed iter-19 final candidates fail C03; the fourth has correct dimensions but is rejected by the exact geometry policies.
