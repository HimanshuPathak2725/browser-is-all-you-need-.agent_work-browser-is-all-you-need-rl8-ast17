# Corner-directed spiral path

Implement the C++17 task in `corner-directed-spiral-path.h`, `corner-directed-spiral-path.cpp`. Return every coordinate of a rows-by-columns rectangle exactly once in clockwise spiral order, starting from the declared Corner. Zero in either dimension returns an empty path. Dimensions whose product overflows size_t reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::spiral_matrix {
enum class Corner { top_left, top_right, bottom_right, bottom_left };
std::optional<std::vector<std::pair<std::size_t,std::size_t>>> clockwise_spiral_path(std::size_t rows, std::size_t columns, Corner start);
}
```

Required edge behavior:

- return shape is explicit
- zero dimensions are empty
- all cells appear once
- corner controls initial coordinate and direction
- product overflow rejects

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
