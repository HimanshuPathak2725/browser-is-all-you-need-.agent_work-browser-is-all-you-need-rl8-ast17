# KGF-C03 implementation report

`verifier_03_roster_mapping.py` checks every named student against distinct top and bottom rows, then repeats the complete roster through bounded, non-null-terminated views. Saved results and reverse sweeps expose state leakage and C-string assumptions.

Trials 2 and 4 pass build/API checks but fail both C03 kernels because their hard-coded row math does not preserve the roster-to-cup relation. The bounded-view probe also rejects a controlled `strcmp(student.data(), ...)` implementation that passes all official cases.
