# Implementing DNF-C05

Range and hit-point checks preserve the useful boundary from the old pack. The added population kernel closes two observed reward gaps: a constructor that copies one generated value into all six fields and a constructor that hard-codes six in-range constants both satisfy the official suite.

The policy samples each field position independently, applies broad support/mean bounds, and caps all-equal characters at 5%. It runs under `_GLIBCXX_ASSERTIONS` and UBSan. The bounds test contract-level generation behavior without requiring a particular random engine, seed, container, or drop-lowest algorithm.
