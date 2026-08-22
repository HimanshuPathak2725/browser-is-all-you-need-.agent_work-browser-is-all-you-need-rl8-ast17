# C03 implementation report: exact API and operators

`verifier_03_exact_api_operators.py` freezes public names and member pointer types, then requires free `date_independent::operator!=` to convert to `bool (*)(const Clock&, const Clock&)`. This directly repairs the coverage omission found in the original Clock policies.

The reference passed 3/3 and the reference-minus-`operator!=` mutant failed C03. That mutant still passed C01, C02, and C06, showing the new failure is not merely a generic compilation signal.

| Kernel | Implementation | Evidence |
| --- | --- | --- |
| C03-A | Normal calls including default `at(hour)` | Compile receipt |
| C03-B | Static assertions for `at`, `plus`, `minus`, conversion, and `==` | Probe/object hashes |
| C03-C | Exact free-function pointer plus runtime unequal comparison | Link/run receipt |

Private constructors and storage remain unconstrained. The policy is exact on the public ABI shape required by the pinned task.
