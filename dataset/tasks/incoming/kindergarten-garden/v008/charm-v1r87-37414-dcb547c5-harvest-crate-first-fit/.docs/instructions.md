# Harvest crate first fit

Implement the C++17 task in `harvest-crate-first-fit.h`, `harvest-crate-first-fit.cpp`. Place positive harvest weights into identical positive-capacity crates using first-fit in input order. Return zero-based crate indices per item; an overweight item or checked-sum overflow rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<std::size_t>> first_fit_harvest_crates(const std::vector<std::int64_t>& weights, std::int64_t capacity);
}
```

Required edge behavior:

- capacity and weights are positive
- overweight items reject
- items retain input order
- lowest fitting crate wins
- new crates are appended

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
