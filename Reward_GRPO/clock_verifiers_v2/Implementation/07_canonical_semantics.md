# C07 implementation report: canonical semantics

`verifier_07_canonical_semantics.py` uses three public black-box executables for whole-day normalization, large signed arithmetic, and normalized equality. It never inspects the candidate's representation or requires the reference algorithm.

The reference passed 3/3. The controlled `24:00` normalization mutant passed C01-C06 but failed C07 and C08, separating semantic correctness from build/API/format shaping.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C07-A | Exact positive/negative whole days and mixed large inputs | Run exit and marker |
| C07-B | Large signed `plus`/`minus`, reversibility, and cross-midnight | Run exit and marker |
| C07-C | Equivalent normalized times, adjacent inequality | Run exit and marker |

This increases confidence for observed modulo-day risk; it remains a selected boundary set, so C08 is still mandatory.
