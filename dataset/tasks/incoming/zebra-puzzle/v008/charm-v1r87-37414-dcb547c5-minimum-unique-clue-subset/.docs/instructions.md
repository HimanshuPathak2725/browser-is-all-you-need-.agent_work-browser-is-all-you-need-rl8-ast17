# Minimum unique clue subset

Implement the C++17 task in `minimum-unique-clue-subset.h`, `minimum-unique-clue-subset.cpp`. Each of up to twenty clues eliminates a bit mask of candidates from a nonempty candidate universe of at most 63 bits. Choose the lexicographically earliest minimum clue-index set that leaves exactly the target candidate.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::zebra_puzzle {
std::optional<std::vector<std::size_t>> minimum_unique_clue_subset(std::uint64_t candidate_mask, std::size_t target, const std::vector<std::uint64_t>& eliminated_by_clue);
}
```

Required edge behavior:

- candidate universe is nonempty and within 63 bits
- target is present
- at most twenty clues
- clues only eliminate non-target candidates
- empty inner vector is also the no-solution sentinel

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
