# CSF-C01 implementation report

`verifier_01_build_integrity.py` combines a header-first compile, independent implementation compile, and real external link/run under exact C++17 warning-as-error flags. The link probe intentionally exercises only construction and normalization so semantic layout failures do not leak into the build signal.

The fourth kernel scans only candidate `crypto_square.h` and `crypto_square.cpp` for explicit hidden-reference and protected-test paths. This closes shortcuts that can still compile and pass visible examples while leaving ordinary standard-library includes and implementation choices unrestricted.
