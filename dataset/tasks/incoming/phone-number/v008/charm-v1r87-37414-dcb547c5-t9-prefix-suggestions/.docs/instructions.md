# T9 prefix suggestions

Implement the C++17 task in `t9-prefix-suggestions.h`, `t9-prefix-suggestions.cpp`. Return up to limit contact names whose lowercase letters encode to a supplied nonempty T9 digit prefix. Names are unique nonempty lowercase words; prefix digits are 2 through 9; results are lexicographic.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::phone_number {
std::optional<std::vector<std::string>> t9_prefix_suggestions(const std::vector<std::string>& contacts, std::string_view prefix, std::size_t limit);
}
```

Required edge behavior:

- prefix is nonempty digits 2 through 9
- contacts are unique lowercase words
- prefix match is digit-wise
- results are lexicographic
- limit may be zero

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
