# House solution certificate

Implement the C++17 task in `solution-certificate.cpp`. Verify category completeness and a proposed item-to-house assignment, returning stable zero-based indices of every violated clue.

The exact public API is:

```cpp
namespace charm::zebra { struct Verification { bool complete; std::vector<std::size_t> violated; }; Verification verify(int,const std::vector<std::vector<std::string>>&,const std::vector<Clue>&,const std::map<std::string,int>&); }
```

Required edge behavior:

- every category item appears once
- each category occupies every house once
- extra assignment items make complete false
- missing clue operands violate that clue
- violated indices preserve input order

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
