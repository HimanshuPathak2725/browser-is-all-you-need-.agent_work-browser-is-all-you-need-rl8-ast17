# KGF-C05 policy: generated oracle and safety

## Contract

Every valid roster position in generated diagrams of widths one through twelve must match an independent byte-position oracle. Results must remain exact across bounded views, reordered calls, and repeated evaluation under runtime safety checks.

| Kernel | Pass condition |
| --- | --- |
| C05-A | Sixty-four generated diagrams per supported width produce 4,992 exact student results |
| C05-B | Thirty-six bounded-view cases remain exact across eight reverse interleavings |

Both probes compile with libstdc++ bounds assertions and non-recovering UBSan. Expected values never use candidate helpers or protected reference code.

## Implementation rationale

`verifier_05_full_domain_oracle.py` generates 64 deterministic diagrams for every supported width and independently selects four bytes for each present student. A second executable uses bounded subviews and reverse interleavings to check repeatability and `string_view` extent.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They reject width-specific wrong answers, nondeterminism, C-string extent misuse, and the controlled width-eight out-of-bounds defect missed by the official examples.
