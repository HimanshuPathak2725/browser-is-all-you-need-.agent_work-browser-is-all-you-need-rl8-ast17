# Stable linked partition

Implement the C++17 task in `stable-partition-repair.h`, `stable-partition-repair.cpp`. Relink existing singly linked nodes so values below the threshold precede the rest while preserving relative order in both partitions.

The exact public API is:

```cpp
namespace charm::list { class StableList { public: void push_back(int); void partition(int); std::vector<int> values() const; }; }
```

Required edge behavior:

- empty list
- all-low and all-high
- values equal to threshold are high
- relative order is stable
- repartitioning is idempotent

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
