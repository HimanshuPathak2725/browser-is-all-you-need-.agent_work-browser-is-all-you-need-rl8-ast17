# CLF-C02 implementation report

`verifier_02_exact_api.py` combines original E01/E05 member-type assertions with v2 C03’s default-call and free-operator probes. It additionally checks that the two-integer constructor is not publicly constructible and that normal copy semantics remain available.

Default arguments cannot be recovered from a function pointer type, so C02-A compiles a real `at(hour)` call. C02-C binds `date_independent::operator!=` to the exact free-function pointer and checks both equal and unequal normalized values.
