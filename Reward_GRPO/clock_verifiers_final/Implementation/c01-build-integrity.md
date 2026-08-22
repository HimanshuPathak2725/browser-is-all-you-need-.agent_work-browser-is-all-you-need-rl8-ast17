# CLF-C01 implementation report

`verifier_01_build_integrity.py` removes four overlapping v2 compile boundaries by retaining one self-contained header probe, one independent implementation build, and one real external link/run. It keeps the original strict signature environment and v2’s explicit C++17 identity check.

The kernel split localizes header/language failures, dependency/warning failures, and link/surface failures without pretending downstream compile cascades are separate root causes. Receipts preserve commands, compiler logs, probe/object/executable hashes, and before/after candidate digests.
