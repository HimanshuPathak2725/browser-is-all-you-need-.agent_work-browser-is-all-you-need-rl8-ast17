# Parallel anagram groups

Implement the C++17 task in `parallel-anagram-groups.h`, `parallel-anagram-groups.cpp`. Group nonempty lowercase words by exact letter multiset using at most the requested positive worker count. Sort words inside groups and sort groups by their first word.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::parallel_letter_frequency {
std::optional<std::vector<std::vector<std::string>>> parallel_anagram_groups(const std::vector<std::string>& words, std::size_t workers);
}
```

Required edge behavior:

- worker count is positive
- words are nonempty lowercase
- workers are bounded by useful jobs
- groups and members are canonical
- empty input is valid

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
