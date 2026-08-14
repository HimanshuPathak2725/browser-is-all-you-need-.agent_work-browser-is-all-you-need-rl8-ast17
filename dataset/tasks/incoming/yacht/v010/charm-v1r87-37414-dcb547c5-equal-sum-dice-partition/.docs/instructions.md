# Equal-sum dice partition

Implement the C++17 task in `equal-sum-dice-partition.cpp`. Partition all positive dice values into two nonempty equal-sum groups. Return the lexicographically earliest vector of indices in the first group among solutions, considering a group and its complement equivalent by requiring index zero in the first group.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::yacht {
std::optional<std::vector<std::size_t>> equal_sum_dice_partition(const std::vector<int>& dice);
}
```

Required edge behavior:

- two to twenty-four positive values
- both groups are nonempty
- index zero breaks complement symmetry
- all dice are used
- no solution returns an empty inner vector

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
