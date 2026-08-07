# Bounded shard frequency

Implement the C++17 task in `bounded-shard-frequency.h`, `bounded-shard-frequency.cpp`. Count ASCII letters case-insensitively across documents with no more than the requested worker count and merge deterministic local arrays.

The exact public API is:

```cpp
namespace charm::frequency { std::array<std::size_t,26> count_bounded(const std::vector<std::string>&,std::size_t); }
```

Required edge behavior:

- zero workers returns zero counts
- empty input
- workers may exceed documents
- non-ASCII-letter bytes are ignored
- results are independent of worker count

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
