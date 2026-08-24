# KGF-C04 instruction: row geometry and cup order

## Contract

For garden widths from one through twelve students, the selected cups must be the student's two consecutive top-row cups followed by the corresponding two bottom-row cups. The newline position determines the second-row stride; no fixed width is valid for every supported diagram.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Four generated patterns across all 12 widths and all present students match an independent oracle |
| C04-B | All 78 width/student positions return exact clover, grass, radishes, violet order |

The probes cover row stride, student offset, partial-roster diagrams, and top/bottom ordering independently of the official examples.
