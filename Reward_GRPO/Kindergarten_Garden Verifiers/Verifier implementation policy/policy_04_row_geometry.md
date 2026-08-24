# KGF-C04 policy: row geometry and cup order

## Contract

For garden widths from one through twelve students, the selected cups must be the student's two consecutive top-row cups followed by the corresponding two bottom-row cups. The newline position determines the second-row stride; no fixed width is valid for every supported diagram.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Four generated patterns across all 12 widths and all present students match an independent oracle |
| C04-B | All 78 width/student positions return exact clover, grass, radishes, violet order |

The probes cover row stride, student offset, partial-roster diagrams, and top/bottom ordering independently of the official examples.

## Implementation rationale

`verifier_04_row_geometry.py` derives the second-row offset from the newline for all roster widths from one through twelve. One probe varies all diagram bytes; the other places four distinct plant values at each student position to isolate exact cup order.

The official suite exercises widths one, two, three, and twelve. C04 closes demonstrated width-four, width-five, width-seven, and width-eight gaps while diagnosing fixed-stride, off-by-one, wrong-student, and swapped-row defects.
