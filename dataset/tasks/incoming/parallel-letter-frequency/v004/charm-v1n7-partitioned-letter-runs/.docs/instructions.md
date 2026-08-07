# Partitioned letter runs

Implement the C++17 task in `partitioned-letter-runs.cpp`. For each input string, compute its longest contiguous run of the same ASCII letter ignoring case, without joining across string boundaries. Process strings through bounded asynchronous partitions and return one length per input in original order. worker_count zero rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::parallel_letter_frequency {
std::optional<std::vector<std::size_t>> parallel_longest_letter_runs(const std::vector<std::string>& inputs, std::size_t worker_count);
}
```

Required edge behavior:

- runs never cross inputs
- case folds ASCII only
- nonletters break runs
- each output slot has one writer
- zero workers reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
