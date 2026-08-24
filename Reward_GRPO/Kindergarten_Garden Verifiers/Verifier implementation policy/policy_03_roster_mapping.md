# KGF-C03 policy: roster mapping and bounded views

## Contract

Alice through Larry must map in the specified alphabetical order to consecutive pairs of cups. Both `std::string_view` parameters must respect their declared extent, and repeated or interleaved queries must remain deterministic.

| Kernel | Pass condition |
| --- | --- |
| C03-A | All 12 students map to exact cups in a distinct full-class diagram |
| C03-B | Non-null-terminated student/diagram views, saved results, and five reverse sweeps remain exact |

Invalid student names and malformed diagrams are outside the pinned task contract.

## Implementation rationale

`verifier_03_roster_mapping.py` checks every named student against distinct top and bottom rows, then repeats the complete roster through bounded, non-null-terminated views. Saved results and reverse sweeps expose state leakage and C-string assumptions.

Trials 2 and 4 pass build/API checks but fail both C03 kernels because their hard-coded row math does not preserve the roster-to-cup relation. The bounded-view probe also rejects a controlled `strcmp(student.data(), ...)` implementation that passes all official cases.
