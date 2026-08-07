# Scorecard assignment

Implement the C++17 task in `scorecard-assignment.cpp`. Assign each five-die roll to a distinct category for maximum total; among equal totals return the lexicographically smallest category-index vector.

The exact public API is:

```cpp
namespace charm::yacht { enum class RuleKind { exact_group, straight, value_sum }; struct Category { RuleKind kind; int argument; }; struct Assignment { int total; std::vector<std::size_t> categories; }; std::optional<Assignment> optimize(const std::vector<std::vector<int>>&,const std::vector<Category>&,int); }
```

Required edge behavior:

- empty rolls score zero
- more rolls than categories reject
- invalid dice reject
- categories cannot repeat
- ties choose lexical index vector

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
