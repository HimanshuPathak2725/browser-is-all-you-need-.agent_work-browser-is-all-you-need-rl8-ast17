# Keyed square transposition

Implement the C++17 task in `keyed-square-transposition.h`, `keyed-square-transposition.cpp`. Normalize ASCII alphanumerics to lowercase, form a near-square padded row grid, permute each row's columns by a validated key, and join rows with spaces.

The exact public API is:

```cpp
namespace charm::cryptosquare { std::optional<std::string> encode_keyed(std::string_view,const std::vector<std::size_t>&); }
```

Required edge behavior:

- empty normalized input requires an empty key
- padding uses lowercase x
- key length equals column count
- key is a complete permutation
- punctuation is discarded

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
