# Partitioned frequency repair

Implement the C++17 task in `partition-frequency-repair.h`, `partition-frequency-repair.cpp`. Partition documents into deterministic contiguous chunks so every document is counted exactly once, including when workers exceed inputs.

The exact public API is:

```cpp
namespace charm::frequency { std::map<char,std::size_t> count_partitioned(const std::vector<std::string>&,std::size_t); }
```

Required edge behavior:

- zero workers
- empty documents
- empty chunks are not created
- remainder documents distribute to early chunks
- ASCII normalization is deterministic

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
