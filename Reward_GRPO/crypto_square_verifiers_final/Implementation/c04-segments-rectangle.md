# CSF-C04 implementation report

`verifier_04_segments_rectangle.py` independently chunks normalized strings at the expected integer column width for every length from 0 through 1024. A second probe uses mixed-source examples and saved reverse-order results to expose padding, dropped remainders, one-character rows, empty-row errors, and state leakage.

The iter-19 trial 2 candidate passes build, API, normalization, and size checks but fails both C04 kernels. This gives a direct diagnostic for its incorrect `plain_text_segments()` indexing before the full cipher oracle is applied.
