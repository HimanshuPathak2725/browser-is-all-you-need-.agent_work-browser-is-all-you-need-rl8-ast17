# DMF-C01 policy: build and dependency integrity

## Contract

Candidate sources must compile as exact ISO C++17 under GCC 13.3 with `-Wall -Wextra -Wpedantic -Werror`. `diamond.h` must be self-contained, `diamond.cpp` must compile independently, an external caller must link and run, and candidate files must not depend on hidden reference or protected test assets.

| Kernel | Pass condition |
| --- | --- |
| C01-A | Include-first header compiles and observes `__cplusplus == 201703L` |
| C01-B | Candidate implementation compiles independently with strict warnings |
| C01-C | External public caller compiles, links, runs, and emits the exact marker |
| C01-D | Candidate source contains no references to hidden examples or protected test files |

This policy consolidates the build and dependency boundaries of original Policies 1, 2, and 4. It does not impose an implementation style or require a particular include-guard mechanism.

## Implementation rationale

`verifier_01_build_integrity.py` replaces overlapping build checks with one include-first header compile, one independent implementation compile, and one real external link/run. Direct GCC invocation removes CMake availability from the per-candidate reward path while preserving the pinned C++17 and warning contract.

The fourth kernel scans only candidate `diamond.h` and `diamond.cpp` for explicit hidden-reference and protected-test paths. This narrow source check closes dependency shortcuts that still compile and pass official behavior; normal standard-library includes and behavior-preserving implementation choices remain unrestricted.
