# Garden capacity audit

Implement the C++17 task in `garden-capacity-audit.h`, `garden-capacity-audit.cpp`. Audit named child plots against per-plant capacities. Child names must be unique, plant names nonempty, counts nonnegative, and a plant may appear at most once per child. Every allocated plant requires a declared nonnegative capacity. Return plants exceeding total capacity ordered by name.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::kindergarten_garden {
struct PlantCount { std::string plant; int count; }; struct ChildPlot { std::string child; std::vector<PlantCount> plants; };
std::optional<std::vector<std::pair<std::string,int>>> audit_garden_capacity(const std::vector<ChildPlot>& plots, const std::map<std::string,int>& capacity);
}
```

Required edge behavior:

- children are unique
- plant appears once per child
- capacity domain is explicit
- counts and capacities are nonnegative
- excess output is lexical

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
