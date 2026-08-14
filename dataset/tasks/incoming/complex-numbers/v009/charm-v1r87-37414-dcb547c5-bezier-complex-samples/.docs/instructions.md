# Complex Bezier samples

Review the supplied C++17 task in `bezier-complex-samples.cpp`. Evaluate a complex Bezier curve at requested exact rational parameters numerator/denominator in [0,1]. The control polygon is nonempty and denominators are positive.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::complex_numbers {
std::optional<std::vector<std::complex<double>>> sample_complex_bezier(const std::vector<std::complex<double>>& control, const std::vector<std::pair<std::int64_t,std::int64_t>>& parameters);
}
```

Required edge behavior:

- control polygon is nonempty
- denominators are positive
- parameters lie in closed unit interval
- request order is preserved
- de Casteljau evaluation is used

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
