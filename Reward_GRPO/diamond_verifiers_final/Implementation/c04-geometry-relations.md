# DMF-C04 implementation report

`verifier_04_geometry_relations.py` consolidates original Policy 6's relational boundary into two dense A-Z probes. One reconstructs expected glyph positions and spaces; the other independently verifies horizontal and vertical symmetry, row order, legal glyph values, and presence of the requested widest-row letter.

All four observed iter-19 final candidates fail C04. The separation from C05 keeps geometry diagnostics readable even though a byte-exact oracle necessarily overlaps these relations.
