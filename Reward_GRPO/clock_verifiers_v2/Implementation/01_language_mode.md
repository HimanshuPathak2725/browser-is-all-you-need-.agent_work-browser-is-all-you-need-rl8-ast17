# C01 implementation report: language mode

`verifier_01_language_mode.py` enforces the pinned C++17 environment through a header probe, independent strict implementation compilation, and a minimal linked caller. It reuses the authenticated shared executor, so compiler identity and protected assets are checked before candidate scoring.

The reference passed 3/3 kernels and the `<=>` mutant failed C01. Because implementation compilation is foundational, missing dependencies, declaration drift, ODR faults, and fatal warnings can also fail this category; C01 is a build gate, not an exclusive cause classifier.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C01-A | Checks `__cplusplus == 201703L` and self-contained header compilation | Object and compiler logs |
| C01-B | Compiles `clock.cpp` with all strict flags | Object hash and stderr |
| C01-C | Links/runs a public caller without asserting Clock semantics | Executable hash and exact marker |

Verified confidence: known-good accepted and observed language mutant rejected. Unverified: other compilers and production-worker invocation. Next check: shadow this gate on real GRPO samples without changing C08 terminal semantics.
