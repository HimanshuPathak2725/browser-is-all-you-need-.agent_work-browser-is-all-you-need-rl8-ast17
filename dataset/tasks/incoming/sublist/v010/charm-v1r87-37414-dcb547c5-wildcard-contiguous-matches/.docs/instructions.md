# Wildcard contiguous matches

Implement the C++17 task in `wildcard-contiguous-matches.h`, `wildcard-contiguous-matches.cpp`. Return all start indices where a nonempty pattern matches contiguously in a text, with '?' matching exactly one byte. Empty text is valid; starts are ascending.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::sublist {
std::optional<std::vector<std::size_t>> wildcard_contiguous_matches(std::string_view text, std::string_view pattern);
}
```

Required edge behavior:

- pattern is nonempty
- question mark consumes one byte
- matches may overlap
- too-long patterns have no matches
- starts are ascending

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
