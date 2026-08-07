# Offset civil clock

Implement the C++17 task in `offset-civil-clock.h`, `offset-civil-clock.cpp`, `offset-civil-clock_detail.cpp`. Normalize arbitrary local hour/minute inputs, preserve the displayed UTC offset, add minutes, and compare daily instants in UTC.

The exact public API is:

```cpp
namespace charm::clockwork { class OffsetClock { public: static OffsetClock at(long long,long long,int); OffsetClock plus_minutes(long long) const; bool same_instant(const OffsetClock&) const; std::string display() const; }; }
```

Required edge behavior:

- negative local inputs
- day wrap in either direction
- offset formatting
- different displays may denote one instant
- offsets differing by a day compare modulo one day

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
