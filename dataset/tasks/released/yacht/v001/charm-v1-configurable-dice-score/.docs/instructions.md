# Configurable dice score

Implement the C++17 task in `configurable-dice-score.h`, `configurable-dice-score.cpp`. Validate exactly five dice and score exact-count groups, consecutive straights, or the sum of a requested face.

The exact public API is:

```cpp
namespace charm::yacht { enum class RuleKind { exact_group, straight, value_sum }; struct Category { RuleKind kind; int argument; }; std::optional<int> score(const std::vector<int>&,int,Category); }
```

Required edge behavior:

- sides is positive
- every die lies in 1..sides
- category arguments validate
- exact group chooses highest matching face
- failed valid categories score zero

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
