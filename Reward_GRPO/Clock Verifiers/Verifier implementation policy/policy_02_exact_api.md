# CLF-C02 policy: exact public API

## Contract

Strict conformance requires namespace `date_independent`, class `clock`, default-callable `at(hour)`, exact member signatures, a private two-integer constructor, const string observation, and namespace-scope free `operator!=` with the pinned parameter and return types.

| Kernel | Pass condition |
| --- | --- |
| C02-A | Default construction surface and reference-returning mutation chain compile |
| C02-B | Member pointers, conversion constness, constructor access, and copy traits match |
| C02-C | Free inequality converts to the exact function pointer and returns correct values |

This policy is strict-contract evidence. Alternate APIs that pass official tests may fail C02 and should only receive negative task reward in `strict` acceptance mode.

## Implementation rationale

`verifier_02_exact_api.py` combines original E01/E05 member-type assertions with v2 C03's default-call and free-operator probes. It additionally checks that the two-integer constructor is not publicly constructible and that normal copy semantics remain available.

Default arguments cannot be recovered from a function pointer type, so C02-A compiles a real `at(hour)` call. C02-C binds `date_independent::operator!=` to the exact free-function pointer and checks both equal and unequal normalized values.
