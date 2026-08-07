# Vanity number repair

Implement the C++17 task in `vanity-number-repair.h`, `vanity-number-repair.cpp`. Normalize classic keypad letters and digits while ignoring conventional separators; preserve a leading plus only for an eleven-digit result.

The exact public API is:

```cpp
namespace charm::phone { std::optional<std::string> normalize_vanity(std::string_view); }
```

Required edge behavior:

- letters map case-insensitively
- plus is only allowed first
- leading plus requires eleven digits
- plain results contain ten or eleven digits
- unknown separators reject

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
