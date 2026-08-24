# DMF-C05 implementation report

`verifier_05_full_domain_oracle.py` generates complete fixed-width output from independent row/column arithmetic and compares every byte for A-Z. A second executable repeats a deliberately interleaved sequence for three rounds and then checks the domain in reverse order.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They catch intermediate-letter defects missed by the official A/B/C/D/Z suite, plus state leakage, nondeterminism, extra bytes, and observed undefined behavior within the pinned domain.
