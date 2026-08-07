# Horner complex polynomial

Review the supplied C++17 task in `horner-complex-polynomial.cpp`. Evaluate a complex polynomial whose coefficients are ordered from highest degree through constant using Horner's method. Empty coefficients denote the zero polynomial. Reject any non-finite coefficient or input component.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::complex_numbers {
std::optional<std::complex<double>> evaluate_complex_polynomial(const std::vector<std::complex<double>>& coefficients, std::complex<double> point);
}
```

Required edge behavior:

- coefficient order is explicit
- empty polynomial is zero
- non-finite inputs reject
- non-finite result rejects
- Horner order is deterministic

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
