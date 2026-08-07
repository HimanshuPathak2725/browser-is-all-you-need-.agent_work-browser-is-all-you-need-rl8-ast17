# Preserving phone redaction

Implement the C++17 task in `preserving-phone-redaction.cpp`. Redact a phone-like string by preserving separators and the final visible_digits decimal digits while replacing every earlier digit with mask. Return both the transformed text and the exact number of digits replaced in RedactedPhone. visible_digits may not exceed the total digit count and mask must not be a decimal digit. Non-digit bytes are preserved exactly.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::phone_number {
struct RedactedPhone { std::string text; std::size_t masked_digits; };
std::optional<RedactedPhone> redact_phone_digits(std::string_view text, std::size_t visible_digits, char mask);
}
```

Required edge behavior:

- separators preserve byte identity
- last digits remain visible
- result reports the masked count
- mask cannot be a digit
- visible count is bounded
- no-digit strings are supported

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
