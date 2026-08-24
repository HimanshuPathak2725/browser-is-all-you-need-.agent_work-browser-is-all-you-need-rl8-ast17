# DNF-C05 policy: character generation

Construct 5,000 characters under runtime-safety instrumentation. Every stored ability must remain in `[3,18]`, and every character must satisfy `hitpoints == 10 + modifier(constitution)`.

A second kernel checks that the constructor actually performs six ability generations instead of copying or hard-coding fields. No more than 5% of characters may have all six abilities equal. Each field position must observe at least 13 distinct values and a mean between `11.5` and `13.0`, broad bounds around the exact four-dice/drop-lowest distribution.

Invariant, independence, distribution, or safety violations are `FAIL`. Evaluator failures are `INVALID`.

## Implementation rationale

Range and hit-point checks preserve the useful boundary from the old pack. The added population kernel closes two observed reward gaps: a constructor that copies one generated value into all six fields and a constructor that hard-codes six in-range constants both satisfy the official suite.

The policy samples each field position independently, applies broad support/mean bounds, and caps all-equal characters at 5%. It runs under `_GLIBCXX_ASSERTIONS` and UBSan. The bounds test contract-level generation behavior without requiring a particular random engine, seed, container, or drop-lowest algorithm.
