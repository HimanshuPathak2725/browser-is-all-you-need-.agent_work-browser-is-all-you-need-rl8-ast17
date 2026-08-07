# Rectangular layer view

Implement the C++17 task in `layer-view-repair.h`, `layer-view-repair.cpp`. Extract a zero-based rectangular perimeter clockwise without duplicating corners or underflowing single-row and single-column layers.

The exact public API is:

```cpp
namespace charm::spiral { std::vector<int> layer_clockwise(const std::vector<std::vector<int>>&,std::size_t); }
```

Required edge behavior:

- empty and ragged matrices reject
- single row
- single column
- nested layer
- layer beyond the interior returns empty

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
