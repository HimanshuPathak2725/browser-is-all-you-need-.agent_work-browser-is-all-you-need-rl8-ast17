# DMF-C05 instruction: full-domain oracle and safety

## Contract

For every input A through Z, the complete returned byte matrix must match an independent fixed-width Diamond oracle. Interleaved and reverse-order calls must remain exact and deterministic under libstdc++ bounds assertions and UBSan.

| Kernel | Pass condition |
| --- | --- |
| C05-A | All 26 complete outputs exactly match the independent byte oracle |
| C05-B | Repeated interleaved calls and a reverse A-Z sweep match the oracle |

Both probes compile with `-D_GLIBCXX_ASSERTIONS`, `-fsanitize=undefined`, and non-recovering UBSan. Invalid-character behavior remains outside the pinned A-Z task contract.
