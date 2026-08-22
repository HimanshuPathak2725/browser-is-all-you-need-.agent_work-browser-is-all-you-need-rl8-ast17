# C02 implementation report: dependency completeness

`verifier_02_dependency_completeness.py` compiles the header first, compiles the implementation independently, and links a caller using the formatting surface. It tests compiler-visible completeness instead of requiring a literal `<iomanip>` token.

The reference passed 3/3 and the missing-`<iomanip>` mutant failed C02. Compile errors necessarily propagate into later policies, so this signal identifies a dependency/build boundary but cannot by itself prove which include is missing.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C02-A | Header-first standalone translation unit | Compile receipt |
| C02-B | Strict independent implementation compile | Compiler stderr and object hash |
| C02-C | Caller exercises conversion and linkage, then prints a fixed marker | Link/run receipt |

Confidence is high for the observed a4 missing-header pattern under GCC 13.3. Equivalent legal include strategies remain accepted.
