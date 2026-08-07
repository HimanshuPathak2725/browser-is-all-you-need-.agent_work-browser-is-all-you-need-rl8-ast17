# Styled hollow diamond

Implement the C++17 task in `styled-hollow-diamond.h`, `styled-hollow-diamond.cpp`. Render a centered odd-height hollow diamond with selected edge and background bytes; literal trailing spaces must be removed.

The exact public API is:

```cpp
namespace charm::diamond { std::optional<std::vector<std::string>> render_hollow(int,char,char); }
```

Required edge behavior:

- height is positive and odd
- height one
- newline style bytes reject
- edge positions are symmetric
- no returned line ends in a space

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
