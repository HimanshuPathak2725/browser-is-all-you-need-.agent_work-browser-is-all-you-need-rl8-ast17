# KGF-C01 instruction: build and dependency integrity

## Contract

Candidate sources must compile as exact ISO C++17 under GCC 13.3 with `-Wall -Wextra -Wpedantic -Werror`. `kindergarten_garden.h` must be self-contained, `kindergarten_garden.cpp` must compile independently, an external caller must link and run, and candidate files must not depend on hidden reference or protected test assets.

| Kernel | Pass condition |
| --- | --- |
| C01-A | Include-first header compiles and observes `__cplusplus == 201703L` |
| C01-B | Candidate implementation compiles independently with strict warnings |
| C01-C | An external public caller compiles, links, runs, and emits the exact marker |
| C01-D | Candidate source contains no references to hidden examples or protected test files |

This policy does not impose an algorithm, source layout, or include-guard mechanism.
