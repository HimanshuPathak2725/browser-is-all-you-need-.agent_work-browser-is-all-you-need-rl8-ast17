# Implementing DNF-C01

The build policy was retained because real model endpoints included missing definitions and header-only non-inline bodies. It uses the shared authenticated `Contract`, compiles the header and implementation independently, and then links an external consumer.

The fourth kernel is a source-boundary control added during consolidation. It rejects direct use of `.meta/example.*`, protected tests, Catch2, or hidden verifier filenames while rechecking the combined candidate digest. This keeps reference leakage and harness coupling out of reward without treating evaluator faults as model failures.
