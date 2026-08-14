# Eastward shadow profile

Implement the C++17 task in `eastward-shadow-profile.cpp`. For nonnegative plant heights in west-to-east order and a positive integer sun slope, mark each plant shadowed when some western plant's remaining height after slope decay is strictly greater than its height.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::kindergarten_garden {
std::optional<std::vector<bool>> eastward_shadow_profile(const std::vector<int>& heights, int slope);
}
```

Required edge behavior:

- heights are nonnegative
- slope is positive
- only western plants cast eastward
- equality is not shadow
- output aligns with input

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
