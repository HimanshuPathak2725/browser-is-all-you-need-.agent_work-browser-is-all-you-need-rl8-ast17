# Best declared rule

Implement the C++17 task in `best-declared-rule.cpp`. Choose the highest-scoring rule from a declared nonempty list using the same four rule names as score_string_rule. Rule names must be unique and valid; ties choose the lexically smaller rule. Return the chosen rule and score after validating all five dice.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::yacht {
std::optional<std::pair<std::string,int>> best_declared_rule(const std::array<int,5>& dice, const std::vector<std::string>& rules);
}
```

Required edge behavior:

- rule list is nonempty
- rules are unique
- unknown rules reject
- higher score wins
- ties are lexical

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
