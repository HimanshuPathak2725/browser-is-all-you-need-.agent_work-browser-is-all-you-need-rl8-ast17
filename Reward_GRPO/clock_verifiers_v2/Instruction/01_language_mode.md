# C01 instruction: C++17 language mode and strict compilation

## Observed failure

Trial a2 submitted defaulted `operator<=>`, a C++20 feature, while the evaluator compiles as C++17. One unsupported construct produced three cascading parser diagnostics.

## Contract

The candidate header and implementation must compile as ISO C++17 with GCC 13.3 using `-Wall -Wextra -Wpedantic -Werror`. No later standard or permissive compiler mode is allowed.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C01-A | `clock.h` is self-contained and compiles in a C++17 caller |
| C01-B | `clock.cpp` compiles alone with strict flags |
| C01-C | A minimal public caller compiles, links, runs, and prints `00:00` |

Missing compiler, wrong version, or protected-asset mismatch is `INVALID`. Candidate diagnostics are `-1`. This is a shaping policy, not terminal correctness.
