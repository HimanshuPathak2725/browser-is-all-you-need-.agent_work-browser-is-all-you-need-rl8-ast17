# Owned chain erasures

Implement the C++17 task in `owned-chain-erasures.h`, `owned-chain-erasures.cpp`. Build a singly linked chain with unique ownership, then erase zero-based positions sequentially. Each position is interpreted in the current chain; an out-of-range position rejects. The implementation must capture the successor before destroying the selected link. Return removed values followed by the remaining values.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::linked_list {
struct ChainEraseResult { std::vector<int> removed; std::vector<int> remaining; };
std::optional<ChainEraseResult> erase_owned_chain_positions(const std::vector<int>& values, const std::vector<std::size_t>& positions);
}
```

Required edge behavior:

- ownership uses unique_ptr
- positions use current chain
- successor is read before unlink
- empty and singleton chains are covered
- out-of-range rejects

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
