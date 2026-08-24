# KGF-C01 implementation report

`verifier_01_build_integrity.py` combines a header-first compile, independent implementation compile, and real external link/run under exact C++17 warning-as-error flags. This directly catches trial 1's missing `<algorithm>` dependency and trial 3's absent public implementation.

The fourth kernel scans only candidate `kindergarten_garden.h` and `kindergarten_garden.cpp` for explicit hidden-reference and protected-test paths. It closes two demonstrated official-suite gaps without restricting normal standard-library includes or implementation style.
