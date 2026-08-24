# CSF-C04 policy: plaintext segments and rectangle relations

## Contract

`plain_text_segments()` must split normalized text into consecutive rows of width `size()`, without padding or dropping the final partial row. Empty normalized text must produce no rows. Repeated and interleaved calls must remain deterministic.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Generated normalized lengths 0 through 1024 match an independent segment oracle and row-width relations |
| C04-B | Empty, perfect, incomplete, numeric, mixed, repeated, saved, and reverse-order cases match exact rows |

Cipher transposition and padded output remain the responsibility of C05 and C06.

## Implementation rationale

`verifier_04_segments_rectangle.py` independently chunks normalized strings at the expected integer column width for every length from 0 through 1024. A second probe uses mixed-source examples and saved reverse-order results to expose padding, dropped remainders, one-character rows, empty-row errors, and state leakage.

The iter-19 trial 2 candidate passes build, API, normalization, and size checks but fails both C04 kernels. This gives a direct diagnostic for its incorrect `plain_text_segments()` indexing before the full cipher oracle is applied.
