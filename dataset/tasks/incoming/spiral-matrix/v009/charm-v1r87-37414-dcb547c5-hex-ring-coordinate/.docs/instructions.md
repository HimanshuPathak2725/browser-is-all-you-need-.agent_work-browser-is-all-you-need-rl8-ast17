# Hex ring coordinate

Implement the C++17 task in `hex-ring-coordinate.h`, `hex-ring-coordinate.cpp`. Return axial (q,r) coordinates after a nonnegative number of steps along a hexagonal outward ring walk: step zero is origin; each ring starts at (ring,0) and walks NW, W, SW, SE, E, NE.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::spiral_matrix {
using AxialPoint = std::pair<int,int>;
std::optional<AxialPoint> hex_ring_coordinate(std::uint64_t steps);
}
```

Required edge behavior:

- steps are zero-based
- ring one occupies steps 1 through 6
- axial direction order is frozen
- ring starts are positive q-axis
- unrepresentable coordinates reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
