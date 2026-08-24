# DMF-C01 implementation report

`verifier_01_build_integrity.py` replaces overlapping build checks with one include-first header compile, one independent implementation compile, and one real external link/run. Direct GCC invocation removes CMake availability from the per-candidate reward path while preserving the pinned C++17 and warning contract.

The fourth kernel scans only candidate `diamond.h` and `diamond.cpp` for explicit hidden-reference and protected-test paths. This narrow source check closes dependency shortcuts that still compile and pass official behavior; normal standard-library includes and behavior-preserving implementation choices remain unrestricted.
