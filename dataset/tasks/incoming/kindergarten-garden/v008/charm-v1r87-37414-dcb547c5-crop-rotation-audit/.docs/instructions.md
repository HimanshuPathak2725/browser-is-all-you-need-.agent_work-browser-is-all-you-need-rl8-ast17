# Crop rotation audit

Implement the C++17 task in `crop-rotation-audit.h`, `crop-rotation-audit.cpp`. Audit rectangular season-by-plot crop labels. Labels are nonempty lowercase words, every season has the same positive plot count, and no plot may repeat a crop within the supplied positive lookback. Return violating season/plot indices.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<std::pair<std::size_t,std::size_t>>> audit_crop_rotation(const std::vector<std::vector<std::string>>& seasons, std::size_t lookback);
}
```

Required edge behavior:

- at least one season and plot
- lookback is positive
- shape is rectangular
- crop labels are lowercase words
- violations are season-major

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
