# Garden patch repair

Implement the C++17 task in `garden-patch-repair.h`, `garden-patch-repair.cpp`. Parse a rectangular grid restricted to unique allowed plant codes, then count clipped half-open rectangular patches.

The exact public API is:

```cpp
namespace charm::garden { class PatchGrid { public: static std::optional<PatchGrid> parse(const std::vector<std::string>&,std::string_view); std::map<char,int> count_patch(int,int,int,int) const; }; }
```

Required edge behavior:

- empty or ragged grid rejects
- unknown and duplicate allowed codes reject
- patch coordinates clip
- reversed rectangles return empty
- counts omit absent codes

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
