# KGF-C03 instruction: roster mapping and bounded views

## Contract

Alice through Larry must map in the specified alphabetical order to consecutive pairs of cups. Both `std::string_view` parameters must respect their declared extent, and repeated or interleaved queries must remain deterministic.

| Kernel | Pass condition |
| --- | --- |
| C03-A | All 12 students map to exact cups in a distinct full-class diagram |
| C03-B | Non-null-terminated student/diagram views, saved results, and five reverse sweeps remain exact |

Invalid student names and malformed diagrams are outside the pinned task contract.
