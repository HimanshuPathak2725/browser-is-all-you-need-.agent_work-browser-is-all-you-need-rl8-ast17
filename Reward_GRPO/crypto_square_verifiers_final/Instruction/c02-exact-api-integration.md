# CSF-C02 instruction: exact API and integration

## Contract

Strict conformance requires a `crypto_square::cipher` constructible from `const std::string&`, copy construction, and the five specified const public methods with exact return types. The header must tolerate repeated inclusion, and all methods must compile, link, and execute across multiple translation units.

| Kernel | Pass condition |
| --- | --- |
| C02-A | Exact const member-function types and required construction properties compile |
| C02-B | Including `crypto_square.h` twice in one translation unit compiles |
| C02-C | Two external translation units plus `crypto_square.cpp` link and call the complete API on empty input |

The policy checks compiler and linker behavior rather than private members, source layout, `#pragma once`, or a named include guard.
