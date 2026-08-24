# CSF-C05 implementation report

`verifier_05_full_domain_oracle.py` computes ASCII normalization, integer dimensions, rows, column-major ciphertext, and padded groups independently. It checks explicit task examples plus generated lengths 0 through 512, then repeats an interleaved sequence containing lengths 255, 997, and 4096 through copied objects and reverse sweeps.

The probes enable libstdc++ bounds assertions and non-recovering UBSan. They close demonstrated original-policy gaps for a length-17 wrong answer and a length-255 out-of-bounds defect while also covering order, separator, padding, nondeterminism, and retained-state faults.
