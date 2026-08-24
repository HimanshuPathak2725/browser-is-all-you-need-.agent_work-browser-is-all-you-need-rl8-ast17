# DNF-C01 policy: build integrity

Evaluate only `dnd_character.h` and `dnd_character.cpp` against the pinned D&D Character task. Authenticate every protected asset before candidate work begins.

The policy requires four independent kernels:

1. the header is self-contained in exact C++17 mode;
2. the implementation compiles with `-Wall -Wextra -Wpedantic -Werror`;
3. an external caller compiles, links, constructs a character, and observes the required hit-point relation;
4. candidate files do not reference the protected tests, hidden verifier, or `.meta/example.*` reference.

A candidate-caused compile, link, or behavior error is `FAIL`. A missing compiler, changed protected asset, malformed evidence, or source mutation during evaluation is `INVALID`.

## Implementation rationale

The build policy was retained because real model endpoints included missing definitions and header-only non-inline bodies. It uses the shared authenticated `Contract`, compiles the header and implementation independently, and then links an external consumer.

The fourth kernel is a source-boundary control added during consolidation. It rejects direct use of `.meta/example.*`, protected tests, Catch2, or hidden verifier filenames while rechecking the combined candidate digest. This keeps reference leakage and harness coupling out of reward without treating evaluator faults as model failures.
