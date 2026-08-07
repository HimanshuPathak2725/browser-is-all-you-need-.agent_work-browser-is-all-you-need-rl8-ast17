# Dial prefix buckets

Implement the C++17 task in `dial-prefix-buckets.h`, `dial-prefix-buckets.cpp`. Group already-normalized digit strings by the longest matching declared dial prefix. Prefixes must be nonempty digit strings with no duplicates; numbers must contain only digits. A number with no prefix match rejects. Return buckets ordered by prefix, with numbers retaining input order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::phone_number {
std::optional<std::map<std::string,std::vector<std::string>>> bucket_by_longest_prefix(const std::vector<std::string>& numbers, const std::vector<std::string>& prefixes);
}
```

Required edge behavior:

- longest prefix wins
- prefix domain is unique
- all text is digit-only
- unmatched numbers reject
- bucket order and item order are deterministic

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
