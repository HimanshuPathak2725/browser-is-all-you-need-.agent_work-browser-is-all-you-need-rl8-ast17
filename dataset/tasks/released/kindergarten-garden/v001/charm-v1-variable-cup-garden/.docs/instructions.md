# Variable cup garden

Implement the C++17 task in `variable-cup-garden.h`, `variable-cup-garden.cpp`. Parse equal-width plant rows for an ordered student list and configurable cups per student; return plants row-major within that student's cups.

The exact public API is:

```cpp
namespace charm::garden { class CupGarden { public: static std::optional<CupGarden> parse(std::vector<std::string>,std::vector<std::string>,std::size_t); std::vector<char> plants(std::string_view) const; }; }
```

Required edge behavior:

- nonempty rows and students
- positive cups
- width equals students times cups
- student names are unique
- unknown student returns empty

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
