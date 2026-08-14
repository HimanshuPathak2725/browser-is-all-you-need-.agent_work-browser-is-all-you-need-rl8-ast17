# Exposure rotation audit

Implement the C++17 task in `exposure-rotation-audit.hpp`. Audit a day-indexed allergen rotation. Each record names one allergen and a nonnegative day; records are strictly day-ordered. Return every adjacent same-allergen pair closer than its declared cooldown, preserving encounter order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::allergies {
struct RotationEntry { int day; std::string allergen; };
std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_exposure_rotation(const std::vector<RotationEntry>& entries, const std::map<std::string,int>& cooldown_days);
}
```

Required edge behavior:

- days are strictly increasing
- all labels have cooldowns
- cooldowns are nonnegative
- the cooldown boundary is allowed
- only consecutive occurrences of one label pair

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
