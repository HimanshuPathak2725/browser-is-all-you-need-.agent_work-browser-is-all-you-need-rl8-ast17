# Standing order calendar

Implement the C++17 task in `standing-order-calendar.hpp`. Move requested nonnegative day indices forward to the next business day. Day zero has a supplied weekday in [0,6], weekdays 5 and 6 are weekends, holidays are nonnegative, and equal settled days aggregate amounts.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::bank_account {
struct StandingOrder { int requested_day; std::int64_t amount; };
std::optional<std::map<int,std::int64_t>> settle_standing_orders(const std::vector<StandingOrder>& orders, int weekday_of_day_zero, const std::set<int>& holidays);
}
```

Required edge behavior:

- day indices and holidays are nonnegative
- weekday is in range
- amounts are positive
- weekends and holidays shift forward
- settled collisions aggregate with overflow checks

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
