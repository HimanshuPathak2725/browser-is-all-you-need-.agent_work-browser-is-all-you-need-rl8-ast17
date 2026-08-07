# Minimum covering slice

Implement the C++17 task in `minimum-covering-slice.h`, `minimum-covering-slice.cpp`. Find the shortest contiguous slice of values whose multiplicities cover every required value multiplicity. Return its half-open [begin,end) indices; ties choose the smaller begin. Empty requirements return [0,0]. If no slice covers the requirements return an empty optional.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::sublist {
std::optional<std::pair<std::size_t,std::size_t>> minimum_covering_slice(const std::vector<int>& values, const std::vector<int>& required);
}
```

Required edge behavior:

- multiplicity matters
- result is half-open
- ties use smaller begin
- empty requirement is zero slice
- missing coverage is empty optional

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
