# Contact source merge

Implement the C++17 task in `contact-source-merge.h`, `contact-source-merge.cpp`. Merge contact records by unique nonempty lowercase name. Lower numeric priority wins; equal priority must agree on the digit-only nonempty number or reject. Return the winning number by name.

The exact case-sensitive public API is:

```cpp
namespace charm::v1r87_37414::phone_number {
struct ContactRecord { std::string name; std::string number; int priority; };
std::optional<std::map<std::string,std::string>> merge_contact_sources(const std::vector<ContactRecord>& records);
}
```

Required edge behavior:

- names are lowercase words
- numbers are nonempty digits
- priorities are nonnegative
- lower priority value wins
- equal-priority conflict rejects

Preserve the namespace, names, signatures, qualifiers, parameter order, and
editable filenames exactly. Use only portable C++17 standard-library
facilities. Return complete whole-file replacements for every editable file.
