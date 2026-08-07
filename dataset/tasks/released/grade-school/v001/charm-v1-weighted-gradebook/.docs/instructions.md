# Weighted gradebook

Implement the C++17 task in `weighted-gradebook.cpp`. Store replaceable assessments and rank students by rounded weighted average in basis points, breaking ties lexically.

The exact public API is:

```cpp
namespace charm::school { class WeightedGradebook { public: bool set(std::string,std::string,int,int); std::optional<int> average_bp(std::string_view) const; std::vector<std::string> ranking() const; }; }
```

Required edge behavior:

- scores are 0..100
- weights are positive
- assessment IDs replace per student
- averages round to nearest basis point
- ranking ties are lexical

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
