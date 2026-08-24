# CSF-C03 implementation report

`verifier_03_normalization_size.py` expands the prior single normalization example into ten ASCII boundary cases, repeated observations, and caller-source mutation after construction. Its size probe uses integer arithmetic for every length from 0 through 4096, avoiding floating-point agreement with candidate code.

The sweep targets punctuation and digit handling, case conversion, raw-versus-normalized sizing, floor/ceiling mistakes, and perfect-square off-by-one defects. Trial 2 passes this focused stage, correctly localizing its observed failure to segmentation and layout.
