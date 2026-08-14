# Tick rate fit

Implement the C++17 task in `tick-rate-fit.cpp`. Fit one exact rational tick rate from strictly increasing real-time samples paired with nondecreasing device ticks. Return the reduced nonnegative numerator and positive denominator, or reject if successive sample slopes differ.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::clock {
struct TickSample { std::int64_t real_time; std::int64_t device_ticks; };
std::optional<std::pair<std::int64_t,std::int64_t>> fit_exact_tick_rate(const std::vector<TickSample>& samples);
}
```

Required edge behavior:

- at least two samples
- real time strictly increases
- device ticks never decrease
- all adjacent reduced slopes match
- zero rate is 0/1

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
