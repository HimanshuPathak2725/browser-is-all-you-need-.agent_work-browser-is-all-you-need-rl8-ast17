# Partitioned posting sum

Implement the C++17 task in `partitioned-posting-sum.hpp`. Sum signed postings using exactly min(worker_count, posting_count) asynchronous partitions. worker_count zero is invalid even for empty input. Detect signed overflow both within partitions and during the deterministic left-to-right reduction.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::bank_account {
std::optional<long long> partitioned_posting_sum(const std::vector<long long>& postings, std::size_t worker_count);
}
```

Required edge behavior:

- zero workers reject
- empty postings sum to zero with workers
- workers are capped
- signed overflow rejects
- reduction order is deterministic

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
