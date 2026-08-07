# Dial plan router

Implement the C++17 task in `dial-plan-router.cpp`. Store unique digit prefixes and choose the longest prefix of a digit-only dial string, returning route name and unmatched subscriber digits.

The exact public API is:

```cpp
namespace charm::phone { class DialPlan { public: bool add(std::string,std::string); std::optional<std::pair<std::string,std::string>> route(std::string_view) const; }; }
```

Required edge behavior:

- empty or nondigit prefixes reject
- duplicate prefix rejects
- nondigit dial string rejects
- longest prefix wins
- subscriber suffix may be empty

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
