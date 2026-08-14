# Manhattan Voronoi owners

Implement the C++17 task in `manhattan-voronoi-owners.h`, `manhattan-voronoi-owners.cpp`. Assign each query point to the unique closest distinct site under Manhattan distance. Return the site index or -1 for a tie; duplicate sites or distance overflow reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::diamond {
using LatticePoint = std::pair<std::int64_t,std::int64_t>;
std::optional<std::vector<int>> manhattan_voronoi_owners(const std::vector<LatticePoint>& sites, const std::vector<LatticePoint>& queries);
}
```

Required edge behavior:

- sites are distinct
- queries preserve order
- ties return -1
- no sites also returns -1
- distance arithmetic is checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
