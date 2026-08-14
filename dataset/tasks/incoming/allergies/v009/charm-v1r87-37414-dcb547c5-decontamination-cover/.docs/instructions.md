# Decontamination cover

Implement the C++17 task in `decontamination-cover.cpp`. Choose the lexicographically earliest minimum-cardinality set of cleaning procedures whose bit masks cover every requested allergen bit. At most twenty procedures and twenty known bits are accepted.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::allergies {
std::optional<std::vector<std::size_t>> minimum_cleaning_cover(const std::vector<std::uint32_t>& procedure_masks, std::uint32_t required_mask, std::uint32_t known_mask);
}
```

Required edge behavior:

- unknown bits reject
- empty requirement needs no procedure
- impossible cover has an empty inner result
- minimum cardinality dominates
- ties use index-vector order

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
