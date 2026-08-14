# Latin row completion

Implement the C++17 task in `latin-row-completion.cpp`. Complete exactly one row of an n by n Latin square over values 1 through n, using zero for blanks. All other rows must be complete, every column must have no duplicate nonzero value, and return the unique completed row or reject ambiguity/impossibility.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::zebra_puzzle {
std::optional<std::vector<int>> complete_unique_latin_row(std::vector<std::vector<int>> grid, std::size_t row);
}
```

Required edge behavior:

- grid is nonempty square
- only target row may contain zero
- values are in range
- rows and columns are Latin
- exactly one completion is required

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
