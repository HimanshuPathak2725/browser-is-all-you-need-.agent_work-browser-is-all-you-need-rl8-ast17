# LFSR cycle report

Implement the C++17 task in `lfsr-cycle-report.hpp`. For a nonempty seed of at most twenty bits and a nonempty unique set of tap indices, repeatedly shift right and insert the XOR of tapped old bits at index zero. Return preperiod and period lengths.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::crypto_square {
std::optional<std::pair<std::size_t,std::size_t>> lfsr_cycle_report(std::string_view seed, const std::vector<std::size_t>& taps);
}
```

Required edge behavior:

- seed is one to twenty binary bits
- taps are nonempty unique valid indices
- tap XOR uses the old state
- shift inserts at index zero
- first repeated state defines the report

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
