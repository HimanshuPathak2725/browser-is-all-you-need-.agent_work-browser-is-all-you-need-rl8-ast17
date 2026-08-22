# C05 implementation report: ODR and linkage

`verifier_05_odr_linkage.py` uses repeated inclusion plus two independently generated caller translation units linked with `clock.cpp`. A second cross-TU probe specifically calls free `operator!=` outside the main caller.

The reference passed 3/3 and the non-inline header-definition mutant failed C05. This reproduces the a8 multiple-definition boundary using linker evidence rather than source-text heuristics.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C05-A | Includes `clock.h` twice in one translation unit | Compile receipt |
| C05-B | Links two callers and candidate implementation | Link/run logs |
| C05-C | Resolves and executes `operator!=` across translation units | Link/run logs |

Any compilation failure blocks linkage and may also fail C05. The category is specific only after prerequisite compile/API gates pass.
