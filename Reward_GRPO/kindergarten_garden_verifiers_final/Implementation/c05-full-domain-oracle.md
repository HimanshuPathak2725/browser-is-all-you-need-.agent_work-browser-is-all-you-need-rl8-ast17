# KGF-C05 implementation report

`verifier_05_full_domain_oracle.py` generates 64 deterministic diagrams for every supported width and independently selects four bytes for each present student. A second executable uses bounded subviews and reverse interleavings to check repeatability and `string_view` extent.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They reject width-specific wrong answers, nondeterminism, C-string extent misuse, and the controlled width-eight out-of-bounds defect missed by the official examples.
