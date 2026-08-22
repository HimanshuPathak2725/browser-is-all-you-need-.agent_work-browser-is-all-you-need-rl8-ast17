# CLF-C01 instruction: build and dependency integrity

## Contract

Candidate sources must compile as exact ISO C++17 under GCC 13.3 with `-Wall -Wextra -Wpedantic -Werror`. `clock.h` must be self-contained, `clock.cpp` must declare its dependencies, and an external caller must compile, link, and execute.

| Kernel | Pass condition |
| --- | --- |
| C01-A | Include-first header compiles and observes `__cplusplus == 201703L` |
| C01-B | Candidate implementation compiles independently with strict warnings |
| C01-C | External public caller compiles, links, runs, and emits the exact marker |

This merges the original E01 compile/link gate with v2 C01, C02, and the compiler-visible part of C04. It intentionally does not diagnose semantic correctness.
