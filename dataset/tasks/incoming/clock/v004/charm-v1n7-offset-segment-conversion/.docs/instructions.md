# Offset segment conversion

Implement the C++17 task in `offset-segment-conversion.cpp`. Convert local minute readings through a schedule of UTC offsets. Each segment begins at a nonnegative local minute and segments must be strictly increasing; the first segment begins at zero. Return normalized UTC minutes in [0,1439] while preserving input order.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::clock {
struct OffsetSegment { int local_begin; int offset_minutes; };
std::optional<std::vector<int>> local_readings_to_utc(const std::vector<int>& local_minutes, const std::vector<OffsetSegment>& segments);
}
```

Required edge behavior:

- schedule starts at zero
- segment starts increase
- readings are nonnegative
- UTC wraps by one day
- input order is stable

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
