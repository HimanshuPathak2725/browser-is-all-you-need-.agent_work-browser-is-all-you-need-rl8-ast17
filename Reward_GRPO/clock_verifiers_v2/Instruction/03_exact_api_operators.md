# C03 instruction: exact public API and operators

## Observed failure

Trial a4 changed the required free inequality operator into a broken member. Trial a8 removed the public declaration after a duplicate-definition failure. Earlier policies did not type-check free `operator!=`.

## Contract

The namespace, class, default-call surface, argument types, return types, reference semantics, constness, conversion operator, member equality, and namespace-scope free inequality operator must match the pinned reference.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C03-A | All required names and default `at(hour)` call compile |
| C03-B | Compile-time member signature assertions pass |
| C03-C | Free `operator!=` converts to `bool (*)(const Clock&, const Clock&)` and works at runtime |

This policy deliberately closes the missing-`operator!=` shaping gap while avoiding constraints on private representation.
