# Splice handle list

Implement the C++17 task in `splice-handle-list.h`, `splice-handle-list.cpp`. Issue stable generation handles, erase by handle, and move an inclusive contiguous handle range before another node without changing live handles.

The exact public API is:

```cpp
namespace charm::list { struct NodeHandle { std::size_t id; std::size_t generation; }; class SpliceList { public: NodeHandle push_back(int); bool erase(NodeHandle); bool splice_before(NodeHandle,NodeHandle,NodeHandle); std::vector<int> values() const; }; }
```

Required edge behavior:

- all handles must be live
- first precedes last
- destination cannot lie inside range
- erasure invalidates only that handle
- splice preserves range order

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
