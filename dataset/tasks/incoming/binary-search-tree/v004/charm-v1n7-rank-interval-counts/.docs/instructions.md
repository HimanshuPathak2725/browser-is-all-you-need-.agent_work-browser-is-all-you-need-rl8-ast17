# Rank interval counts

Review the supplied C++17 task in `rank-interval-counts.hpp`. Given insertion keys with duplicates rejected, answer half-open rank intervals [first,last) over the sorted tree contents. Return sums for valid intervals and reject the complete request if any bound is reversed or exceeds the node count.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::binary_search_tree {
struct RankInterval { std::size_t first; std::size_t last; };
std::optional<std::vector<long long>> tree_rank_interval_sums(const std::vector<int>& insertion_keys, const std::vector<RankInterval>& intervals);
}
```

Required edge behavior:

- duplicates reject
- intervals are half-open
- empty intervals sum to zero
- invalid bounds reject all
- negative keys are supported

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Preserve every byte of every editable file. Do not return file listings, fenced blocks, diffs, or replacements. If the supplied implementation satisfies the contract, return exactly `No changes are required.`
