# Binary CRC syndrome

Implement the C++17 task in `binary-crc-syndrome.cpp`. Compute the modulo-two polynomial remainder of a nonempty binary message after appending degree zero bits, using a binary generator whose first and last bits are one and length is at least two.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::crypto_square {
std::optional<std::string> binary_crc_syndrome(std::string_view message, std::string_view generator);
}
```

Required edge behavior:

- message is nonempty binary
- generator has degree at least one
- generator endpoints are one
- division is modulo two
- remainder width is degree

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
