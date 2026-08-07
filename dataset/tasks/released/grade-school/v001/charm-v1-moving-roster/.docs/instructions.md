# Moving roster

Implement the C++17 task in `moving-roster.h`, `moving-roster.cpp`. Maintain exactly one nonnegative grade per unique student, move enrolled students atomically, and return deterministic grade and school listings.

The exact public API is:

```cpp
namespace charm::school { class MovingRoster { public: bool enroll(std::string,int); bool move(std::string,int); std::vector<std::string> grade(int) const; std::vector<std::pair<int,std::string>> roster() const; }; }
```

Required edge behavior:

- empty names and negative grades reject
- duplicate enrollment rejects
- move requires an existing student
- grade names are lexical
- roster sorts by grade then name

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
