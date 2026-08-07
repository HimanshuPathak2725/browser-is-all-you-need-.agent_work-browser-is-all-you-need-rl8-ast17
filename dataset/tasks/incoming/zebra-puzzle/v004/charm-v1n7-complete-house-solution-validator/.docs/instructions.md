# Complete house solution validator

Implement the C++17 task in `complete-house-solution-validator.h`, `complete-house-solution-validator.cpp`. Validate a completed assignment of named attributes to houses. Every row must contain exactly attribute_count distinct nonempty values, and every value must appear in exactly one house globally. Equality clues require two values in the same house; neighbor clues require houses whose indices differ by one. Unknown clue values reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::zebra_puzzle {
struct ValuePairClue { std::string first; std::string second; };
bool validate_complete_house_solution(const std::vector<std::vector<std::string>>& houses, std::size_t attribute_count, const std::vector<ValuePairClue>& equal_house, const std::vector<ValuePairClue>& neighbors);
}
```

Required edge behavior:

- row width is exact
- values are globally unique
- clues use known distinct values
- equality uses same house
- neighbor distance is exactly one

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
