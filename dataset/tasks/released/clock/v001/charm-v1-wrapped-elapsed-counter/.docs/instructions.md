# Wrapped elapsed counter

Implement the C++17 task in `wrapped-elapsed-counter.hpp`. Compute elapsed minutes on a 24-hour counter from two valid minute observations and an explicit nonnegative wrap count; reject inconsistent or overflowing observations.

The exact public API is:

```cpp
namespace charm::clockwork { std::optional<long long> elapsed(int,int,long long); }
```

Required edge behavior:

- zero elapsed is valid
- end before start needs at least one wrap
- multiple wraps
- invalid minute fields
- multiplication overflow

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
