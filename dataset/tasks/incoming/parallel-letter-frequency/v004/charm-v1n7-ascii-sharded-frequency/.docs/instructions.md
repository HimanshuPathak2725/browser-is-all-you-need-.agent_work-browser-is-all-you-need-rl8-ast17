# ASCII sharded frequency

Implement the C++17 task in `ascii-sharded-frequency.h`, `ascii-sharded-frequency.cpp`. Count ASCII letters case-insensitively across input strings with exactly min(worker_count,input_count) asynchronous shards. The exact result type is std::unordered_map<char,std::size_t>. worker_count zero rejects; empty input with positive workers returns an empty map. Non-ASCII bytes and nonletters are ignored.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::parallel_letter_frequency {
std::optional<std::unordered_map<char,std::size_t>> sharded_ascii_frequency(const std::vector<std::string>& inputs, std::size_t worker_count);
}
```

Required edge behavior:

- unordered_map type is exact
- zero workers reject
- worker count is capped with matching size types
- shards own local maps
- join is deterministic in counts

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
