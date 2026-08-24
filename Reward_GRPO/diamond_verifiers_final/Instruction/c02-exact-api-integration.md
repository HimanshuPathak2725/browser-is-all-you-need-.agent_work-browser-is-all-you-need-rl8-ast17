# DMF-C02 instruction: exact API and integration

## Contract

Strict conformance requires the exact free-function type `std::vector<std::string> diamond::rows(char)`. The header must tolerate repeated inclusion, and the public symbol must compile, link, and execute across multiple translation units.

| Kernel | Pass condition |
| --- | --- |
| C02-A | `decltype(&diamond::rows)` exactly matches `std::vector<std::string> (*)(char)` |
| C02-B | Including `diamond.h` twice in one translation unit compiles |
| C02-C | Two external translation units plus `diamond.cpp` link and call the API |

The policy checks compiler and linker behavior rather than requiring `#pragma once`, a named guard, `inline`, or any particular source layout.
