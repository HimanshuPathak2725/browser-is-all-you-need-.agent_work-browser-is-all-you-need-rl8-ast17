# Mergeable frequency

Implement the C++17 task in `mergeable-frequency.cpp`. Merge each identified 26-letter count shard at most once, atomically rejecting duplicate IDs or size_t overflow.

The exact public API is:

```cpp
namespace charm::frequency { class MergeCounter { public: bool merge(std::string,const std::array<std::size_t,26>&); std::size_t count(char) const; std::size_t merged_shards() const; }; }
```

Required edge behavior:

- empty shard ID rejects
- duplicate shard is inert
- overflow rejects the whole shard
- queries are ASCII case-insensitive
- nonletters report zero

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
