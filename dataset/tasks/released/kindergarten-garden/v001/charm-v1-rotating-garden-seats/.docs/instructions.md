# Rotating garden seats

Implement the C++17 task in `rotating-garden-seats.cpp`. Keep plants at fixed equal-size seat blocks while student ownership rotates by signed day using floor-mod semantics.

The exact public API is:

```cpp
namespace charm::garden { class RotatingGarden { public: RotatingGarden(std::vector<std::string>,std::vector<char>); std::vector<char> plants_for(std::string_view,long long) const; }; }
```

Required edge behavior:

- day zero
- positive wrap
- negative rotation
- unknown student
- malformed unequal seat blocks return empty

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
