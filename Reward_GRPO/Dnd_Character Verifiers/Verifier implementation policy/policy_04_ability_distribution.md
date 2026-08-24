# DNF-C04 policy: ability distribution

The task requires four independent fair six-sided rolls with the lowest roll discarded. A range-only check cannot distinguish that rule from constant, uniform, three-dice, or correlated generators, so this policy checks both support and distribution.

The support kernel evaluates 20,000 calls, requires every result in `[3,18]`, at least 14 observed values, a low-tail value no greater than 5, and a high-tail value at least 17. The distribution kernel evaluates 100,000 calls against the exact enumeration of all 1,296 four-die outcomes. It requires total-variation distance at most `0.06` and mean error at most `0.20`.

Both kernels run with libstdc++ assertions and undefined-behavior sanitization. Candidate violations are `FAIL`; tool, timeout, or evidence faults are `INVALID`.

## Implementation rationale

The old verifier and official suite checked only output range. On the common corpus they accepted constant-10, uniform `[3,18]`, three-dice, and alternating-extreme implementations. Iter-19 trial 2 also initially summed all four dice and produced 19.

The final policy first provides a cheap support signal, then independently enumerates all 1,296 legal four-die outcomes and compares a 100,000-call candidate histogram. The total-variation and mean thresholds are deliberately wider than ordinary sampling noise; eight independent valid implementations passed, including `std::rand`, `std::mt19937`, `thread_local`, per-call seeded, source-defined, and inline-header forms.
