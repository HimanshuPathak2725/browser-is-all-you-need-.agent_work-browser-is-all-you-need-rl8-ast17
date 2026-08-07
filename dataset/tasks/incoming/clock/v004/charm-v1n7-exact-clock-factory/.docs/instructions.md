# Exact clock factory

Implement the C++17 task in `exact-clock-factory.h`, `exact-clock-factory.cpp`, `exact-clock-factory_detail.cpp`. Provide the exact case-sensitive ExactClock type and make_exact_clock factory. The factory accepts arbitrary signed hours and minutes and normalizes to a 24-hour day. ExactClock exposes minutes_since_midnight, equality, and signed minute addition with wraparound.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::clock {
class ExactClock { public: explicit ExactClock(int minute); int minutes_since_midnight() const; ExactClock operator+(long long delta) const; bool operator==(const ExactClock& other) const; private: int minute_; };
ExactClock make_exact_clock(long long hours, long long minutes);
}
```

Required edge behavior:

- API spelling is exact
- hours and minutes are signed
- normalization is modulo one day
- addition wraps both ways
- equality compares normalized time

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
