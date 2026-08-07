# Scaled safe division

Implement the C++17 task in `scaled-safe-division.hpp`. Divide two complex values using a scale-aware real arithmetic formula. A denominator whose magnitude is at most epsilon rejects, as do negative epsilon and non-finite components. Return a finite quotient only.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::complex_numbers {
std::optional<std::complex<double>> divide_complex_scaled(std::complex<double> numerator, std::complex<double> denominator, double epsilon);
}
```

Required edge behavior:

- epsilon is nonnegative
- near-zero denominator rejects
- all components are finite
- zero numerator is valid
- result must remain finite

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
