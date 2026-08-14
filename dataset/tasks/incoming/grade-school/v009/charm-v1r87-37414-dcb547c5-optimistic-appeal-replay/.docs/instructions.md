# Optimistic appeal replay

Implement the C++17 task in `optimistic-appeal-replay.cpp`. Replay score appeals carrying a student, expected version, and signed delta. Every student begins at the supplied nonnegative score and version zero; a version mismatch or a score outside [0,100] rejects the whole replay.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::grade_school {
struct Appeal { std::string student; std::size_t expected_version; int delta; };
std::optional<std::map<std::string,std::pair<int,std::size_t>>> replay_grade_appeals(const std::map<std::string,int>& initial, const std::vector<Appeal>& appeals);
}
```

Required edge behavior:

- initial scores are 0 through 100
- students must already exist
- versions start at zero
- expected versions must match
- updates remain in range

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
