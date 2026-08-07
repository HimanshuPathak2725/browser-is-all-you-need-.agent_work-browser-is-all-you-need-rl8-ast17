# Deterministic shard top letter

Implement the C++17 task in `deterministic-shard-top-letter.h`, `deterministic-shard-top-letter.cpp`. Count lowercase ASCII letters over byte shards and return the most frequent letter and count. Each shard is processed asynchronously; ties select the lexically smaller letter. worker_count must be positive. If there are no lowercase letters, return an empty inner optional.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::parallel_letter_frequency {
std::optional<std::optional<std::pair<char,std::size_t>>> parallel_top_lowercase(const std::vector<std::string>& shards, std::size_t worker_count);
}
```

Required edge behavior:

- only lowercase bytes count
- tie breaks lexically
- outer optional is configuration validity
- inner optional is data presence
- partitions are local

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
