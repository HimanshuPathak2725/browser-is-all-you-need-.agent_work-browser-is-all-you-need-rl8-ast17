# Diamond intersection lattice count

Implement the C++17 task in `diamond-intersection-lattice-count.cpp`. Count integer lattice points contained in every closed Manhattan diamond. Radii must be nonnegative and at most 500; an empty set of diamonds rejects as unbounded.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::diamond {
struct ManhattanDiamond { int row; int col; int radius; };
std::optional<std::size_t> diamond_intersection_lattice_count(const std::vector<ManhattanDiamond>& diamonds);
}
```

Required edge behavior:

- input is nonempty
- radii are in the bounded public domain
- diamonds are closed
- empty intersection returns zero
- count is over integer lattice points

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
