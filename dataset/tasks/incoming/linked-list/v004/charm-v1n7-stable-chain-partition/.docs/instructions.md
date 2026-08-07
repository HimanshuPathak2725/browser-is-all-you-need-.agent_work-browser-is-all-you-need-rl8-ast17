# Stable chain partition

Implement the C++17 task in `stable-chain-partition.cpp`. Build an owned chain and stably partition its nodes around pivot without copying node values: values less than pivot precede values greater than or equal to pivot while relative order in each group remains unchanged. Return the resulting sequence and the number of relinked nodes.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::linked_list {
struct ChainPartition { std::vector<int> values; std::size_t relinked; };
ChainPartition stable_partition_owned_chain(const std::vector<int>& values, int pivot);
}
```

Required edge behavior:

- values are not copied during relink
- partition is stable
- every node is relinked once
- empty and singleton work
- pivot belongs to high group

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
