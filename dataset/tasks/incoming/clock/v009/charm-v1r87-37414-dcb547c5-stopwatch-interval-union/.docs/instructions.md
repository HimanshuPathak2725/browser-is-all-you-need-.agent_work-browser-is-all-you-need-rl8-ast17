# Stopwatch interval union

Implement the C++17 task in `stopwatch-interval-union.hpp`. Normalize closed stopwatch intervals with nonnegative endpoints. Sort them and merge overlaps or intervals whose integer endpoints touch; return merged intervals and their inclusive total tick count.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::clock {
std::optional<std::pair<std::vector<std::pair<std::int64_t,std::int64_t>>,std::int64_t>> merge_stopwatch_intervals(std::vector<std::pair<std::int64_t,std::int64_t>> intervals);
}
```

Required edge behavior:

- intervals are closed
- endpoints are nonnegative
- adjacent integer intervals merge
- output is sorted and disjoint
- total count is overflow-checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
