# C04 implementation report: header/source consistency

`verifier_04_header_source_consistency.py` compiles `clock.cpp` independently and links two external callers that compose the complete public surface. Runtime markers assert successful construction/linkage without re-scoring exact formatting.

The reference passed 3/3 and the missing-constructor-declaration mutant failed C04. The test is representation-neutral; it detects the a5 class/source drift through normal compiler and linker rules.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C04-A | Independent implementation object build | Strict compiler receipt |
| C04-B | External factory plus mutation call chain | Executable and marker |
| C04-C | External calls to conversion, equality, and inequality | Executable and marker |

API omissions can overlap C03/C05, which is expected. No private member name or reference layout is inspected.
