# Generation overwrite ring

Implement the C++17 task in `generation-overwrite-ring.h`, `generation-overwrite-ring.cpp`, `generation-overwrite-ring_detail.cpp`. A fixed-capacity overwrite ring returns generation-tagged handles; overwrites invalidate only old handles and snapshots stay oldest-first.

The exact public API is:

```cpp
namespace charm::ring { struct Handle { std::size_t slot; std::size_t generation; }; class OverwriteRing { public: explicit OverwriteRing(std::size_t); Handle push(int); std::optional<int> read(Handle) const; std::vector<int> snapshot() const; }; }
```

Required edge behavior:

- zero capacity
- partially filled order
- wraparound order
- stale handles
- new handles remain valid

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
