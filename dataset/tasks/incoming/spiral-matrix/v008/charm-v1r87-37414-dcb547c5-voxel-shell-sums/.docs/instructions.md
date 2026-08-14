# Voxel shell sums

Implement the C++17 task in `voxel-shell-sums.h`, `voxel-shell-sums.cpp`. For a nonempty rectangular 3D integer box, sum cells by zero-based shell depth, where depth is the minimum distance to any of the six faces. Return outer-to-inner checked int64 sums.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::spiral_matrix {
std::optional<std::vector<std::int64_t>> voxel_shell_sums(const std::vector<std::vector<std::vector<int>>>& box);
}
```

Required edge behavior:

- box is nonempty in every dimension
- shape is rectangular
- depth uses all six faces
- output is outer-to-inner
- sums are int64 checked

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
