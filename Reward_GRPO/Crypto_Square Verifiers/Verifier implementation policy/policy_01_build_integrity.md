# CSF-C01 policy: build and dependency integrity

## Contract

Candidate sources must compile as exact ISO C++17 under GCC 13.3 with `-Wall -Wextra -Wpedantic -Werror`. `crypto_square.h` must be self-contained, `crypto_square.cpp` must compile independently, an external caller must link and run, and candidate files must not depend on hidden reference or protected test assets.

| Kernel | Pass condition |
| --- | --- |
| C01-A | Include-first header compiles and observes `__cplusplus == 201703L` |
| C01-B | Candidate implementation compiles independently with strict warnings |
| C01-C | An external caller constructs the public type, links, runs, and emits the exact marker |
| C01-D | Candidate source contains no references to hidden examples or protected test files |

This policy consolidates build and dependency checks without imposing a private representation or a particular include-guard style.

## Implementation rationale

`verifier_01_build_integrity.py` combines a header-first compile, independent implementation compile, and real external link/run under exact C++17 warning-as-error flags. The link probe intentionally exercises only construction and normalization so semantic layout failures do not leak into the build signal.

The fourth kernel scans only candidate `crypto_square.h` and `crypto_square.cpp` for explicit hidden-reference and protected-test paths. This closes shortcuts that can still compile and pass visible examples while leaving ordinary standard-library includes and implementation choices unrestricted.
