# Wrapped logical slice repair

Implement the C++17 task in `wrapped-slice-repair.hpp`. Keep the newest fixed-capacity sequence and slice its logical oldest-first view; negative starts count from the logical end and lengths clamp.

The exact public API is:

```cpp
namespace charm::ring { class SliceRing { public: explicit SliceRing(std::size_t); void push(int); std::vector<int> slice(long long,std::size_t) const; std::size_t size() const; }; }
```

Required edge behavior:

- empty and zero-capacity rings
- overwrite changes logical origin
- -1 selects the last item
- very negative starts clamp to zero
- large lengths clamp to available values

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
