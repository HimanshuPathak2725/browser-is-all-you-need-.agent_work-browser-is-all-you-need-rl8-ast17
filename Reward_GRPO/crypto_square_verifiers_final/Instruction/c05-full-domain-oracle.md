# CSF-C05 instruction: full-domain oracle and safety

## Contract

Normalization, size, plaintext rows, unpadded ciphertext, and normalized padded ciphertext must all match an independent Crypto Square oracle. Results must remain exact across large inputs, copying, saved values, repeated calls, and interleaved construction under runtime safety checks.

| Kernel | Pass condition |
| --- | --- |
| C05-A | Ten explicit cases and generated normalized lengths 0 through 512 match all five public results exactly |
| C05-B | An interleaved sequence through length 4096, including length 255, remains exact across copies and four reverse sweeps |

Both probes compile with libstdc++ bounds assertions and non-recovering UBSan. Expected values are calculated without using candidate helpers or protected reference code.
