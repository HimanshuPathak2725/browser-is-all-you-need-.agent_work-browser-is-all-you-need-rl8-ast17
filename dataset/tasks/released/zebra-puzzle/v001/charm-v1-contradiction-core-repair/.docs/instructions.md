# Contradiction core repair

Implement the C++17 task in `contradiction-core-repair.h`, `contradiction-core-repair.cpp`. Return a deterministic inclusion-minimal list of clue indices whose selected clues are unsatisfiable; return empty when all clues are satisfiable.

The exact public API is:

```cpp
namespace charm::zebra { std::vector<std::size_t> contradiction_core(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&); }
```

Required edge behavior:

- satisfiable puzzle returns empty
- all output indices refer to input clues
- the selected set is unsatisfiable
- removing any selected clue restores satisfiability
- output is deterministic

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
