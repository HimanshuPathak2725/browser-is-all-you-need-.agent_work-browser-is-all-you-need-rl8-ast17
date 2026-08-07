# Joker rule repair

Implement the C++17 task in `joker-rule-repair.h`, `joker-rule-repair.cpp`. Score five dice with at most one zero joker, choosing one replacement face consistently to maximize the selected category.

The exact public API is:

```cpp
namespace charm::yacht { enum class JokerCategory { yacht, full_house, four_kind, choice }; std::optional<int> joker_score(const std::array<int,5>&,JokerCategory); }
```

Required edge behavior:

- more than one joker rejects
- nonjoker faces are 1..6
- replacement is one face
- full house requires 2+3
- choice maximizes the sum

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
