# Diamond erosion depths

Implement the C++17 task in `diamond-erosion-depths.hpp`. For a nonempty rectangular grid of '#' and '.', give every filled cell its one-based Manhattan erosion depth: distance to the nearest empty cell or to outside the grid. Empty cells receive zero.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::diamond {
std::optional<std::vector<std::vector<int>>> diamond_erosion_depths(const std::vector<std::string>& grid);
}
```

Required edge behavior:

- grid is nonempty rectangular
- only two cell symbols are accepted
- outside is empty
- empty cells have zero
- filled depth is one-based

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
