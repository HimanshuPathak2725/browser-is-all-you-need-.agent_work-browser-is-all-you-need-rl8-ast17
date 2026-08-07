# Cyclic interval overlap

Implement the C++17 task in `cyclic-interval-overlap.hpp`. Count overlapping minutes between two half-open daily intervals. Each interval is described by a normalized start minute and a duration from 0 through 1440; intervals may cross midnight. Invalid starts or durations reject.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::clock {
struct DailyInterval { int start_minute; int duration; };
std::optional<int> cyclic_overlap_minutes(DailyInterval first, DailyInterval second);
}
```

Required edge behavior:

- intervals are half-open
- midnight crossing is cyclic
- zero duration is empty
- duration 1440 is full day
- starts are normalized inputs

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
