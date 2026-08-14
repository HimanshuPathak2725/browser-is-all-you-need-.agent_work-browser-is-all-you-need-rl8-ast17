# Hermitian energy

Implement the C++17 task in `hermitian-energy.hpp`. Validate a square Hermitian complex matrix within the supplied nonnegative tolerance and compute the real quadratic energy x* A x. Dimension mismatch or a residual imaginary energy above tolerance rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::complex_numbers {
std::optional<double> hermitian_quadratic_energy(const std::vector<std::vector<std::complex<double>>>& matrix, const std::vector<std::complex<double>>& x, double tolerance);
}
```

Required edge behavior:

- matrix is square and dimension-matched
- tolerance is nonnegative
- Hermitian symmetry is tolerance-bound
- empty energy is zero
- imaginary residual must be within tolerance

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
