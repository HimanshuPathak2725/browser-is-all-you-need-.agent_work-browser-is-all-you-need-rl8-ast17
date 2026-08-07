# Typed plant row parser

Implement the C++17 task in `typed-plant-row-parser.h`, `typed-plant-row-parser.cpp`. Parse two equal-width plant rows into the exact PlantCode enum and assign each consecutive pair of columns to one child. Children are supplied in mapping order and count must equal width/2. Reject odd widths, invalid plant bytes, duplicate or empty child names, and inconsistent dimensions.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::kindergarten_garden {
enum class PlantCode { clover, grass, radish, violet }; using ChildPlants = std::pair<std::string,std::array<PlantCode,4>>;
std::optional<std::vector<ChildPlants>> parse_typed_garden(std::string_view top, std::string_view bottom, const std::vector<std::string>& children);
}
```

Required edge behavior:

- enum names are exact
- two rows have equal even width
- children follow supplied order
- plant bytes are closed-domain
- names are unique

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
