# Meal mask filter

Implement the C++17 task in `meal-mask-filter.hpp`. Select meal identifiers whose declared allergen masks do not intersect a blocked mask. Meal identifiers must be distinct and nonempty, and every meal mask may use only bits from known_mask. Return selected identifiers in input order; malformed domains reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::allergies {
struct MaskedMeal { std::string id; std::uint32_t allergens; };
std::optional<std::vector<std::string>> meals_avoiding_mask(const std::vector<MaskedMeal>& meals, std::uint32_t known_mask, std::uint32_t blocked_mask);
}
```

Required edge behavior:

- blocked bits must be known
- meal bits must be known
- identifiers are unique
- zero masks are supported
- input order is preserved

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
