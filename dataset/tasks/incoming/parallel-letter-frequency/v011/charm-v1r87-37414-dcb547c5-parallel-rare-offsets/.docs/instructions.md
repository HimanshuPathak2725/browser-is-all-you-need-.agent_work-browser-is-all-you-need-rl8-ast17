# Parallel rare offsets

Implement the C++17 task in `parallel-rare-offsets.h`, `parallel-rare-offsets.cpp`. Across lowercase lines, return every global byte offset whose letter occurs exactly once in the whole corpus. Lines are concatenated without separators and offsets are ascending; use positive workers.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::vector<std::size_t>> parallel_rare_letter_offsets(const std::vector<std::string>& lines, std::size_t workers);
}
```

Required edge behavior:

- worker count is positive
- lines contain lowercase letters only
- concatenation has no separators
- rarity is corpus-global
- offsets are ascending

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
