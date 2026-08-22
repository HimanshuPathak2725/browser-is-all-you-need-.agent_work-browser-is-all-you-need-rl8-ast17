# CLF-C02 instruction: exact public API

## Contract

Strict conformance requires namespace `date_independent`, class `clock`, default-callable `at(hour)`, exact member signatures, a private two-integer constructor, const string observation, and namespace-scope free `operator!=` with the pinned parameter and return types.

| Kernel | Pass condition |
| --- | --- |
| C02-A | Default construction surface and reference-returning mutation chain compile |
| C02-B | Member pointers, conversion constness, constructor access, and copy traits match |
| C02-C | Free inequality converts to the exact function pointer and returns correct values |

This policy is strict-contract evidence. Alternate APIs that pass official tests may fail C02 and should only receive negative task reward in `strict` acceptance mode.
