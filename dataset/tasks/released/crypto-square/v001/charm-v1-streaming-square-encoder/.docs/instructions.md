# Streaming square encoder

Implement the C++17 task in `streaming-square-encoder.cpp`. Accumulate normalized chunks, choose rectangular dimensions only on the first finish, emit space-separated padded columns, and make finish idempotent.

The exact public API is:

```cpp
namespace charm::cryptosquare { class StreamingEncoder { public: bool append(std::string_view); std::string finish(); bool finished() const; }; }
```

Required edge behavior:

- punctuation is ignored
- empty finish
- padding preserves a rectangle
- append after finish rejects
- repeated finish is byte-identical

Preserve every namespace, public name, parameter order, return type, qualifier,
and editable filename exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
