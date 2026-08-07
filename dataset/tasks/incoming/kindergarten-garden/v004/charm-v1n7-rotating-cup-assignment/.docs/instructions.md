# Rotating cup assignment

Implement the C++17 task in `rotating-cup-assignment.cpp`. Assign a flat sequence of plant labels to children in rotating order beginning at signed start_child. Child names must be unique and nonempty, labels must be nonempty, and no assignment is possible when children are empty unless labels are also empty. Return each child and its assigned labels in original child order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::kindergarten_garden {
std::optional<std::vector<std::pair<std::string,std::vector<std::string>>>> assign_rotating_cups(const std::vector<std::string>& children, const std::vector<std::string>& labels, long long start_child);
}
```

Required edge behavior:

- signed start normalizes
- children retain input order
- labels retain per-child order
- empty domain behavior is explicit
- names and labels are validated

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
