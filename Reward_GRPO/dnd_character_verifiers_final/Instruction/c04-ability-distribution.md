# DNF-C04: ability distribution

The task requires four independent fair six-sided rolls with the lowest roll discarded. A range-only check cannot distinguish that rule from constant, uniform, three-dice, or correlated generators, so this policy checks both support and distribution.

The support kernel evaluates 20,000 calls, requires every result in `[3,18]`, at least 14 observed values, a low-tail value no greater than 5, and a high-tail value at least 17. The distribution kernel evaluates 100,000 calls against the exact enumeration of all 1,296 four-die outcomes. It requires total-variation distance at most `0.06` and mean error at most `0.20`.

Both kernels run with libstdc++ assertions and undefined-behavior sanitization. Candidate violations are `FAIL`; tool, timeout, or evidence faults are `INVALID`.
