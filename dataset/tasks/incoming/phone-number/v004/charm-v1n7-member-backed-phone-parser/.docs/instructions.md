# Member-backed phone parser

Implement the C++17 task in `member-backed-phone-parser.h`, `member-backed-phone-parser.cpp`. Parse ASCII phone text into the exact NormalizedPhone class. Ten national digits are accepted; eleven digits are accepted only when the first is 1 and that prefix is removed. A single x or X introduces a nonempty digit-only extension. Area and exchange codes may not begin with 0 or 1. The constructor must transfer values into member state exposed by const accessors.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::phone_number {
class NormalizedPhone { public: NormalizedPhone(std::string national_digits, std::string extension_digits); const std::string& digits() const; const std::string& extension() const; private: std::string digits_; std::string extension_; };
std::optional<NormalizedPhone> parse_normalized_phone(std::string_view text);
}
```

Required edge behavior:

- member state is observable through const accessors
- country prefix is exactly one
- area and exchange starts are bounded
- extension syntax is unique
- alphabetic noise rejects

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
