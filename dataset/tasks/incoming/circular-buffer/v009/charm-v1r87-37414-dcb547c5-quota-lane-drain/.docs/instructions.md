# Quota lane drain

Implement the C++17 task in `quota-lane-drain.hpp`. Drain FIFO lanes in repeating lane-index order. Each visit may emit up to that lane's positive quota; zero-lane input is valid. Reject lane/quota size mismatch or any zero quota.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::circular_buffer {
std::optional<std::vector<int>> drain_fifo_lanes(std::vector<std::deque<int>> lanes, const std::vector<std::size_t>& quotas);
}
```

Required edge behavior:

- lane and quota counts match
- all quotas are positive
- empty lanes are skipped
- lane order repeats
- FIFO order is preserved per lane

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
