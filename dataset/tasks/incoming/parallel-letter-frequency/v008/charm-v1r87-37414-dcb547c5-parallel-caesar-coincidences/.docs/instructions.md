# Parallel Caesar coincidences

Implement the C++17 task in `parallel-caesar-coincidences.cpp`. For equal-length lowercase strings, count aligned character matches under every Caesar shift 0 through 25 using positive workers. Return 26 counts in shift order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::array<std::size_t,26>> parallel_caesar_coincidences(std::string_view left, std::string_view right, std::size_t workers);
}
```

Required edge behavior:

- worker count is positive
- strings have equal length
- bytes are lowercase letters
- all 26 shifts are computed
- output index equals shift

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
