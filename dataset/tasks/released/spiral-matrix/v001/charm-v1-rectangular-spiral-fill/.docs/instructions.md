# Rectangular spiral fill

Implement the C++17 task in `rectangular-spiral-fill.h`, `rectangular-spiral-fill.cpp`. Fill an arbitrary rectangular matrix clockwise from a selected corner, advancing by the caller's start value and step.

The exact public API is:

```cpp
namespace charm::spiral { enum class Corner { top_left, top_right, bottom_right, bottom_left }; std::vector<std::vector<long long>> fill(std::size_t,std::size_t,Corner,long long,long long); }
```

Required edge behavior:

- zero dimension returns empty
- one-row and one-column rectangles
- all four corners choose their clockwise initial direction
- negative or zero step
- every cell is filled once

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
