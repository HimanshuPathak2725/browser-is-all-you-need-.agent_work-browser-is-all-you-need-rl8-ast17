# DMF-C04 policy: geometry relations

## Contract

Every A-Z result must satisfy exact glyph-count, glyph-position, leading/inner/trailing-space, horizontal-symmetry, vertical-symmetry, and ascending/descending-letter relations.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Every byte position contains the expected glyph or ASCII space, with one or two glyphs as required |
| C04-B | Every row and result satisfies horizontal/vertical symmetry, letter order, and widest-row membership |

Expected positions are calculated independently from row and input indices. Failures may overlap C03, C05, or C06; policy scores must not be summed as independent fault counts.

## Implementation rationale

`verifier_04_geometry_relations.py` consolidates original Policy 6's relational boundary into two dense A-Z probes. One reconstructs expected glyph positions and spaces; the other independently verifies horizontal and vertical symmetry, row order, legal glyph values, and presence of the requested widest-row letter.

All four observed iter-19 final candidates fail C04. The separation from C05 keeps geometry diagnostics readable even though a byte-exact oracle necessarily overlaps these relations.
