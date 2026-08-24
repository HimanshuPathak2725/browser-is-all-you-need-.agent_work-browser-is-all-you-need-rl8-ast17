# CSF-C03 instruction: normalization and size

## Contract

Normalization must remove ASCII whitespace and punctuation, retain ASCII letters and digits, and lowercase letters. The result must be owned by the cipher object rather than borrowed from mutable caller storage. `size()` must return the smallest column count whose square covers the normalized length.

| Kernel | Pass condition |
| --- | --- |
| C03-A | Ten empty, punctuation, case, digit, whitespace, and source-isolation cases normalize exactly across repeats |
| C03-B | Every normalized length from 0 through 4096 returns the exact integer column count, including square boundaries |

This policy isolates normalization and dimension defects; row segmentation and cipher layout are owned by C04 and C05.
