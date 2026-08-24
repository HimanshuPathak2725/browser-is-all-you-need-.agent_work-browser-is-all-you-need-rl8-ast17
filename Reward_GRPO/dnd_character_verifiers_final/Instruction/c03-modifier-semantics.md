# DNF-C03: modifier semantics

Evaluate the complete contract domain used by generated characters, scores 3 through 18. Scores 3 through 9 must use mathematical floor semantics, including the negative odd cases that C++ truncating integer division gets wrong. Scores 10 through 18 must match the exact zero and positive table.

Each half of the table is repeated to reject stateful or nondeterministic modifier implementations. The policy does not impose behavior outside the pinned 3-to-18 ability domain.

Any wrong or unstable value is `FAIL`; infrastructure or authenticated-evidence failure is `INVALID`.
