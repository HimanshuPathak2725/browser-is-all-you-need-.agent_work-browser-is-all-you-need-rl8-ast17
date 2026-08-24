# DNF-C03 policy: modifier semantics

Evaluate the complete contract domain used by generated characters, scores 3 through 18. Scores 3 through 9 must use mathematical floor semantics, including the negative odd cases that C++ truncating integer division gets wrong. Scores 10 through 18 must match the exact zero and positive table.

Each half of the table is repeated to reject stateful or nondeterministic modifier implementations. The policy does not impose behavior outside the pinned 3-to-18 ability domain.

Any wrong or unstable value is `FAIL`; infrastructure or authenticated-evidence failure is `INVALID`.

## Implementation rationale

Iter-19 trial 3 used `(score - 10) / 2`, producing `-3, -2, -1, 0` for scores `3, 5, 7, 9`. A later D&D-trained checkpoint used `(score - 11) / 2`, fixing the negative side while breaking positive even scores.

The final policy therefore splits the exact 3-to-18 table into negative-floor and nonnegative kernels. Repetition catches hidden state without extending the public contract beyond scores that an ability can generate.
