# Extension canonicalizer

Implement the C++17 task in `extension-canonicalizer.h`, `extension-canonicalizer.cpp`. Canonicalize a North-American ten-digit number with optional x/ext extension, rejecting letters in the main number and invalid area or exchange prefixes.

The exact public API is:

```cpp
namespace charm::phone { struct CanonicalPhone { std::string number; std::string extension; }; std::optional<CanonicalPhone> canonicalize(std::string_view); }
```

Required edge behavior:

- optional leading country code 1
- area and exchange begin 2..9
- extension is 1..6 digits
- letters before extension reject
- unsupported punctuation rejects

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
