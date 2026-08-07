# Cursor gap list

Implement the C++17 task in `cursor-gap-list.cpp`. Edit a sequence through a gap cursor. Moves outside [0,size] reject, insertion occurs before the gap and leaves the gap after the inserted item, and erase removes the next item.

The exact public API is:

```cpp
namespace charm::list { class GapList { public: bool move(long long); void insert(int); std::optional<int> erase_next(); std::vector<int> values() const; std::size_t cursor() const; }; }
```

Required edge behavior:

- empty erase
- negative cursor move
- past-end move
- insert advances the gap
- erase keeps the gap index

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
