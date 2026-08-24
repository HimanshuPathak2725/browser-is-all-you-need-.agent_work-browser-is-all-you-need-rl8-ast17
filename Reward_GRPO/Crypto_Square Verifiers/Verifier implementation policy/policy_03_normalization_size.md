# CSF-C03 policy: normalization and size

## Contract

Normalization must remove ASCII whitespace and punctuation, retain ASCII letters and digits, and lowercase letters. The result must be owned by the cipher object rather than borrowed from mutable caller storage. `size()` must return the smallest column count whose square covers the normalized length.

| Kernel | Pass condition |
| --- | --- |
| C03-A | Ten empty, punctuation, case, digit, whitespace, and source-isolation cases normalize exactly across repeats |
| C03-B | Every normalized length from 0 through 4096 returns the exact integer column count, including square boundaries |

This policy isolates normalization and dimension defects; row segmentation and cipher layout are owned by C04 and C05.

## Implementation rationale

`verifier_03_normalization_size.py` expands the prior single normalization example into ten ASCII boundary cases, repeated observations, and caller-source mutation after construction. Its size probe uses integer arithmetic for every length from 0 through 4096, avoiding floating-point agreement with candidate code.

The sweep targets punctuation and digit handling, case conversion, raw-versus-normalized sizing, floor/ceiling mistakes, and perfect-square off-by-one defects. Trial 2 passes this focused stage, correctly localizing its observed failure to segmentation and layout.
