# Selected DFT bins

Implement the C++17 task in `selected-dft-bins.h`, `selected-dft-bins.cpp`, `selected-dft-bins_detail.cpp`. Compute only requested DFT bins of a nonempty complex signal using the negative-angle convention. Bin indices must be unique and in range; return values in request order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::complex_numbers {
std::optional<std::vector<std::complex<double>>> selected_dft_bins(const std::vector<std::complex<double>>& signal, const std::vector<std::size_t>& bins);
}
```

Required edge behavior:

- signal is nonempty
- bins are unique and valid
- negative exponential convention
- request order is preserved
- empty bin request is valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
