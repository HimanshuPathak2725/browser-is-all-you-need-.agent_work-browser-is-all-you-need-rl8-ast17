# DMF-C05 policy: full-domain oracle and safety

## Contract

For every input A through Z, the complete returned byte matrix must match an independent fixed-width Diamond oracle. Interleaved and reverse-order calls must remain exact and deterministic under libstdc++ bounds assertions and UBSan.

| Kernel | Pass condition |
| --- | --- |
| C05-A | All 26 complete outputs exactly match the independent byte oracle |
| C05-B | Repeated interleaved calls and a reverse A-Z sweep match the oracle |

Both probes compile with `-D_GLIBCXX_ASSERTIONS`, `-fsanitize=undefined`, and non-recovering UBSan. Invalid-character behavior remains outside the pinned A-Z task contract.

## Implementation rationale

`verifier_05_full_domain_oracle.py` generates complete fixed-width output from independent row/column arithmetic and compares every byte for A-Z. A second executable repeats a deliberately interleaved sequence for three rounds and then checks the domain in reverse order.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They catch intermediate-letter defects missed by the official A/B/C/D/Z suite, plus state leakage, nondeterminism, extra bytes, and observed undefined behavior within the pinned domain.
