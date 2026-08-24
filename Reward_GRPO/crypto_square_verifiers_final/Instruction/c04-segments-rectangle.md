# CSF-C04 instruction: plaintext segments and rectangle relations

## Contract

`plain_text_segments()` must split normalized text into consecutive rows of width `size()`, without padding or dropping the final partial row. Empty normalized text must produce no rows. Repeated and interleaved calls must remain deterministic.

| Kernel | Pass condition |
| --- | --- |
| C04-A | Generated normalized lengths 0 through 1024 match an independent segment oracle and row-width relations |
| C04-B | Empty, perfect, incomplete, numeric, mixed, repeated, saved, and reverse-order cases match exact rows |

Cipher transposition and padded output remain the responsibility of C05 and C06.
