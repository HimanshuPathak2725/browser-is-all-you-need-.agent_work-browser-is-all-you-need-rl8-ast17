# CSF-C05 policy: full-domain oracle and safety

## Contract

Normalization, size, plaintext rows, unpadded ciphertext, and normalized padded ciphertext must all match an independent Crypto Square oracle. Results must remain exact across large inputs, copying, saved values, repeated calls, and interleaved construction under runtime safety checks.

| Kernel | Pass condition |
| --- | --- |
| C05-A | Ten explicit cases and generated normalized lengths 0 through 512 match all five public results exactly |
| C05-B | An interleaved sequence through length 4096, including length 255, remains exact across copies and four reverse sweeps |

Both probes compile with libstdc++ bounds assertions and non-recovering UBSan. Expected values are calculated without using candidate helpers or protected reference code.

## Implementation rationale

`verifier_05_full_domain_oracle.py` computes ASCII normalization, integer dimensions, rows, column-major ciphertext, and padded groups independently. It checks explicit task examples plus generated lengths 0 through 512, then repeats an interleaved sequence containing lengths 255, 997, and 4096 through copied objects and reverse sweeps.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They close demonstrated original-policy gaps for a length-17 wrong answer and a length-255 out-of-bounds defect while also covering order, separator, padding, nondeterminism, and retained-state faults.
