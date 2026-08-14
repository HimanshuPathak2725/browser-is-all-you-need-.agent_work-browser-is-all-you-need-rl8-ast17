# Weekly recurrence wait

Implement the C++17 task in `weekly-recurrence-wait.h`, `weekly-recurrence-wait.cpp`, `weekly-recurrence-wait_detail.cpp`. Given a current minute in a repeating 10080-minute week and candidate minute slots, return the strictly positive wait to the next occurrence. Slots must be unique and in range; an empty schedule rejects.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::clock {
std::optional<int> wait_to_next_weekly_slot(int current_minute, const std::vector<int>& slots);
}
```

Required edge behavior:

- current and slots are week-relative
- slots are unique
- the wait is strictly positive
- same slot means next week
- empty schedules reject

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
