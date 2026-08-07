# Tolerant subsequence repair

Implement the C++17 task in `tolerant-subsequence-repair.h`, `tolerant-subsequence-repair.cpp`. Greedily return the earliest ordered host indices whose values differ from pattern values by at most a nonnegative tolerance, without signed-overflow bugs.

The exact public API is:

```cpp
namespace charm::sublist { std::optional<std::vector<std::size_t>> tolerant_subsequence(const std::vector<long long>&,const std::vector<long long>&,long long); }
```

Required edge behavior:

- negative tolerance rejects
- empty pattern succeeds
- indices strictly increase
- earliest greedy match
- extreme signed values compare safely

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
