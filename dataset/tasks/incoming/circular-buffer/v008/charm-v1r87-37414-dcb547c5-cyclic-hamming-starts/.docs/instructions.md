# Cyclic Hamming starts

Implement the C++17 task in `cyclic-hamming-starts.cpp`. Return every start index in a nonempty circular text whose length-sized cyclic window differs from a nonempty pattern in at most the supplied mismatch budget. A pattern may wrap around the text multiple times.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::circular_buffer {
std::optional<std::vector<std::size_t>> cyclic_hamming_starts(std::string_view text, std::string_view pattern, std::size_t mismatch_budget);
}
```

Required edge behavior:

- both strings are nonempty
- starts are text indices
- pattern can wrap repeatedly
- budget is inclusive
- results are ascending

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
