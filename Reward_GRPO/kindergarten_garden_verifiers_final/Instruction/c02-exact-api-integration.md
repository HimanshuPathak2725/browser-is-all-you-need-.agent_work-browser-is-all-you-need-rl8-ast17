# KGF-C02 instruction: exact API and integration

## Contract

`Plants` must be a `char`-backed enum with exact `C`, `G`, `R`, and `V` values. `plants` must have the exact type `std::array<Plants, 4> (*)(std::string_view, std::string_view)`. The header must tolerate repeated inclusion, and the public symbol must link across multiple translation units.

| Kernel | Pass condition |
| --- | --- |
| C02-A | Enum representation, enumerator values, and function-pointer type match exactly |
| C02-B | Including `kindergarten_garden.h` twice in one translation unit compiles |
| C02-C | Two external translation units plus candidate implementation compile, link, and call the API |

The policy checks compiler and linker behavior rather than private implementation choices.
