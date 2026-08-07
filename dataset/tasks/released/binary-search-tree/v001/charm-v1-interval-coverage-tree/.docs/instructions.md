# Interval coverage index

Implement the C++17 task in `interval-coverage-tree.cpp`. Index closed labeled integer intervals and return containing labels by shortest interval then lexical label.

The exact public API is:

```cpp
namespace charm::bst { class IntervalIndex { public: bool add(int,int,std::string); std::vector<std::string> containing(int) const; }; }
```

Required edge behavior:

- reversed or unlabeled intervals reject
- endpoints are inclusive
- negative coordinates work
- equal lengths tie lexically
- no matches returns empty

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
