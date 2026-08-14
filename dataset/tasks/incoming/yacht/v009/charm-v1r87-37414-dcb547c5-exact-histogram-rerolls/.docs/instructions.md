# Exact histogram rerolls

Implement the C++17 task in `exact-histogram-rerolls.h`, `exact-histogram-rerolls.cpp`. Given dice faces and a target count for every face 1 through sides, return the minimum dice that must be rerolled to make the exact histogram possible. Sides is positive, all faces are in range, counts are nonnegative, and target total equals dice count.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::yacht {
std::optional<std::size_t> minimum_exact_histogram_rerolls(const std::vector<int>& dice, int sides, const std::vector<std::size_t>& target_counts);
}
```

Required edge behavior:

- sides is positive
- target has one count per face
- target total equals dice count
- dice faces are in range
- maximum already-useful dice are retained

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
