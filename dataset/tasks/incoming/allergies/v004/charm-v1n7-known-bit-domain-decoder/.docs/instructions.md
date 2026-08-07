# Known bit-domain decoder

Implement the C++17 task in `known-bit-domain-decoder.h`, `known-bit-domain-decoder.cpp`, `known-bit-domain-decoder_detail.cpp`. Decode a score through an explicit allergen-bit domain. Domain entries must have distinct nonzero single-bit values and distinct nonempty names. A score containing any unknown bit is invalid; score zero decodes to an empty list. Return names ordered by ascending bit value.

The exact case-sensitive public API is:

```cpp
namespace charm::v1n7::allergies {
struct AllergenBit { std::uint32_t bit; std::string name; };
std::optional<std::vector<std::string>> decode_known_allergies(std::uint32_t score, const std::vector<AllergenBit>& domain);
}
```

Required edge behavior:

- zero score is empty
- unknown score bits reject
- domain bits are powers of two
- domain names and bits are unique
- output follows numeric bit order

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
