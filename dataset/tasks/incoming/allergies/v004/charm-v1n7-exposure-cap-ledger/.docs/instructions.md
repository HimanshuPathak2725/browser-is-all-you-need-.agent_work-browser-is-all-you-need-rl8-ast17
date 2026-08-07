# Exposure cap ledger

Implement the C++17 task in `exposure-cap-ledger.cpp`. Accumulate named nonnegative exposure units against explicit per-allergen caps. Caps and event names must be nonempty and unique; every event must name a declared cap. Return the allergens whose totals exceed their caps, ordered by descending excess and then name. Invalid input rejects the ledger.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::allergies {
struct ExposureEvent { std::string allergen; int units; };
std::optional<std::vector<std::pair<std::string,int>>> exceeded_exposure_caps(const std::vector<std::pair<std::string,int>>& caps, const std::vector<ExposureEvent>& events);
}
```

Required edge behavior:

- negative units reject
- events require declared caps
- duplicate caps reject
- integer overflow rejects
- excess ordering is deterministic

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
