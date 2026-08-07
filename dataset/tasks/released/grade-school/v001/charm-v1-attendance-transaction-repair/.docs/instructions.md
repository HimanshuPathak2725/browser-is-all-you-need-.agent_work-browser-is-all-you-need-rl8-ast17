# Attendance transaction repair

Implement the C++17 task in `attendance-transaction-repair.h`, `attendance-transaction-repair.cpp`. Record complete daily attendance batches atomically. Every known student appears exactly once or no totals change.

The exact public API is:

```cpp
namespace charm::school { class AttendanceBook { public: bool add_student(std::string); bool record_day(const std::vector<std::pair<std::string,bool>>&); std::pair<int,int> totals(std::string_view) const; }; }
```

Required edge behavior:

- duplicate students reject
- unknown students reject
- missing students reject
- invalid batches leave all totals unchanged
- unknown total query returns {-1,-1}

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
