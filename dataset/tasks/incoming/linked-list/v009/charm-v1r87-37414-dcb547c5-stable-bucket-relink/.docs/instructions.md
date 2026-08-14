# Stable bucket relink

Implement the C++17 task in `stable-bucket-relink.h`, `stable-bucket-relink.cpp`. Relink array-indexed nodes into one chain ordered by nonnegative bucket number while preserving original index order within each bucket. Return the head and next-index array; bucket values above the declared count reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::linked_list {
std::optional<std::pair<int,std::vector<int>>> stable_bucket_relink(const std::vector<std::size_t>& buckets, std::size_t bucket_count);
}
```

Required edge behavior:

- bucket indices are in range
- empty nodes allow zero buckets
- bucket order is ascending
- within-bucket order is stable
- the final node links to -1

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
