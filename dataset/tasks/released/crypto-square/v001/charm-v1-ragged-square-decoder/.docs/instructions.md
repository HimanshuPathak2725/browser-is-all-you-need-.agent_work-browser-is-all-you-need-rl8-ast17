# Ragged square decoder

Implement the C++17 task in `ragged-square-decoder.hpp`. Decode whitespace-separated columns row-wise, accepting only the legal long-columns-first height pattern and rejecting malformed symbols.

The exact public API is:

```cpp
namespace charm::cryptosquare { std::optional<std::string> decode_columns(std::string_view); }
```

Required edge behavior:

- empty input decodes empty
- column heights differ by at most one
- long columns precede short columns
- non-alphanumeric column data rejects
- multiple whitespace separators are allowed

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
