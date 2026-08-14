# Closed conversion cycle

Implement the C++17 task in `closed-conversion-cycle.cpp`. Apply an ordered currency cycle of exact positive rational rates. Every intermediate numerator product must fit int64 and divide exactly; report whether the final amount equals the initial positive amount.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::bank_account {
std::optional<bool> closes_exact_conversion_cycle(std::int64_t amount, const std::vector<std::pair<std::int64_t,std::int64_t>>& rates);
}
```

Required edge behavior:

- the opening amount is positive
- rates have positive terms
- every step is integral
- overflow rejects
- an empty cycle closes

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
