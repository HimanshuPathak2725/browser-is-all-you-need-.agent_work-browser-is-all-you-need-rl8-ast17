# Transactional ring batches

Implement the C++17 task in `transactional-ring-batches.cpp`. Apply batches of integer pushes to a bounded ring. Each batch is atomic: if reject_on_full is true and the complete batch cannot fit, leave the ring unchanged and mark that batch rejected; otherwise overwrite oldest elements as needed. Return the final ring and one acceptance flag per batch.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::circular_buffer {
struct RingBatchResult { std::vector<int> values; std::vector<bool> accepted; };
std::optional<RingBatchResult> apply_ring_batches(std::size_t capacity, bool reject_on_full, const std::vector<std::vector<int>>& batches);
}
```

Required edge behavior:

- batch rejection rolls back
- overwrite mode accepts long batches
- zero capacity rejects values
- empty batches are accepted
- flags align with batches

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
