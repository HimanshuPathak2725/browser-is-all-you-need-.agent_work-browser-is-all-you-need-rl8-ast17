# House constraint engine

Implement the C++17 task in `house-constraint-engine.h`, `house-constraint-engine.cpp`. Solve a small category-permutation house puzzle and return an assignment only when exactly one assignment satisfies all equality, adjacency, and immediately-left clues.

The exact public API is:

```cpp
namespace charm::zebra { enum class ClueKind { same_house, adjacent, immediately_left }; struct Clue { ClueKind kind; std::string a; std::string b; }; std::optional<std::map<std::string,int>> solve_unique(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&); }
```

Required edge behavior:

- positive house count
- each category has exactly one item per house
- item names are globally unique
- every clue name exists
- zero or multiple solutions return nullopt

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
