# Wildcard segment relation

Implement the C++17 task in `wildcard-segment-relation.h`, `wildcard-segment-relation.cpp`. Classify two integer patterns where the designated wildcard in either input matches one value; proper containment is contiguous.

The exact public API is:

```cpp
namespace charm::sublist { enum class Relation { equal, subpattern, superpattern, unequal }; Relation wildcard_relation(const std::vector<int>&,const std::vector<int>&,int); }
```

Required edge behavior:

- two empty patterns are equal
- wildcard works in either operand
- proper containment requires differing lengths
- empty is a proper subpattern of nonempty
- first matching segment is sufficient

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
