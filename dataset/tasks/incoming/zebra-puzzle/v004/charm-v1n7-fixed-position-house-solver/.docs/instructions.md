# Fixed position house solver

Implement the C++17 task in `fixed-position-house-solver.h`, `fixed-position-house-solver.cpp`. Use the exact solve_house_assignment entry point and HouseAssignment result type. Assign each distinct nonempty item to one of house_count positions. Fixed clues name an item and position; unclued items fill remaining positions lexically. Reject contradictions, unknown items, duplicate item names, invalid positions, or house_count above 10.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::zebra_puzzle {
struct FixedHouseClue { std::string item; std::size_t position; }; struct HouseAssignment { std::vector<std::string> item_at_position; };
std::optional<HouseAssignment> solve_house_assignment(std::size_t house_count, const std::vector<std::string>& items, const std::vector<FixedHouseClue>& clues);
}
```

Required edge behavior:

- solve entry point is exact
- result type is explicit
- domain size equals houses
- clues are noncontradictory
- unclued fill is lexical and bounded

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
