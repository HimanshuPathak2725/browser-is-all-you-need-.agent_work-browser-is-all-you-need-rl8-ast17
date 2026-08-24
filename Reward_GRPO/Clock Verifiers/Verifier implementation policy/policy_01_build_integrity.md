# CLF-C01 policy: build and dependency integrity

## Contract

Candidate sources must compile as exact ISO C++17 under GCC 13.3 with `-Wall -Wextra -Wpedantic -Werror`. `clock.h` must be self-contained, `clock.cpp` must declare its dependencies, and an external caller must compile, link, and execute.

| Kernel | Pass condition |
| --- | --- |
| C01-A | Include-first header compiles and observes `__cplusplus == 201703L` |
| C01-B | Candidate implementation compiles independently with strict warnings |
| C01-C | External public caller compiles, links, runs, and emits the exact marker |

This merges the original E01 compile/link gate with v2 C01, C02, and the compiler-visible part of C04. It intentionally does not diagnose semantic correctness.

## Implementation rationale

`verifier_01_build_integrity.py` removes four overlapping v2 compile boundaries by retaining one self-contained header probe, one independent implementation build, and one real external link/run. It keeps the original strict signature environment and v2's explicit C++17 identity check.

The kernel split localizes header/language failures, dependency/warning failures, and link/surface failures without pretending downstream compile cascades are separate root causes. Receipts preserve commands, compiler logs, probe/object/executable hashes, and before/after candidate digests.
