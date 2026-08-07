# Cyclic window containment

Implement the C++17 task in `cyclic-window-containment.cpp`. Return the earliest host index where a pattern occurs across the circular boundary; nonempty patterns longer than the host are forbidden.

The exact public API is:

```cpp
namespace charm::sublist { std::optional<std::size_t> cyclic_find(const std::vector<int>&,const std::vector<int>&); }
```

Required edge behavior:

- empty pattern returns zero
- empty host cannot contain nonempty
- pattern length cannot exceed host
- matches may cross the boundary
- earliest start wins

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
