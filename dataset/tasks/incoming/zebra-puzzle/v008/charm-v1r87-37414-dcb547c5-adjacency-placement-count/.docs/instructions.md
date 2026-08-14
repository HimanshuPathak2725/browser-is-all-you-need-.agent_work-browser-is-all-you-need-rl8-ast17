# Adjacency placement count

Implement the C++17 task in `adjacency-placement-count.h`, `adjacency-placement-count.cpp`. Count permutations of n named items satisfying fixed-position and unordered-adjacency clues. Names are unique nonempty strings, positions are zero-based, clue names must exist, and duplicate constraints reject. n is at most ten.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::zebra_puzzle {
struct FixedPlacement { std::string item; std::size_t position; };
std::optional<std::size_t> count_adjacency_placements(std::vector<std::string> items, const std::vector<FixedPlacement>& fixed, const std::vector<std::pair<std::string,std::string>>& adjacent);
}
```

Required edge behavior:

- at most ten unique named items
- fixed positions and names are unique
- adjacency is unordered
- duplicate clues reject
- the empty permutation counts once

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
