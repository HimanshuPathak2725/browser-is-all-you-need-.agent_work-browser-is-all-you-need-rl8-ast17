# DMF-C04 instruction: geometry relations

## Contract

Every A-Z result must satisfy exact glyph-count, glyph-position, leading/inner/trailing-space, horizontal-symmetry, vertical-symmetry, and ascending/descending-letter relations.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Every byte position contains the expected glyph or ASCII space, with one or two glyphs as required |
| C04-B | Every row and result satisfies horizontal/vertical symmetry, letter order, and widest-row membership |

Expected positions are calculated independently from row and input indices. Failures may overlap C03, C05, or C06; policy scores must not be summed as independent fault counts.
