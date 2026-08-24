# KGF-C02 policy: exact API and integration

## Contract

`Plants` must be a `char`-backed enum with exact `C`, `G`, `R`, and `V` values. `plants` must have the exact type `std::array<Plants, 4> (*)(std::string_view, std::string_view)`. The header must tolerate repeated inclusion, and the public symbol must link across multiple translation units.

| Kernel | Pass condition |
| --- | --- |
| C02-A | Enum representation, enumerator values, and function-pointer type match exactly |
| C02-B | Including `kindergarten_garden.h` twice in one translation unit compiles |
| C02-C | Two external translation units plus candidate implementation compile, link, and call the API |

The policy checks compiler and linker behavior rather than private implementation choices.

## Implementation rationale

`verifier_02_exact_api_integration.py` uses compile-time enum and function-pointer assertions, followed by repeated-include and multi-translation-unit probes. This distinguishes the required `string_view` API and `char`-backed enum from interfaces that remain callable through implicit conversion.

The integration probes catch missing guards and non-inline header definitions that the single-translation-unit official build accepts. A legal named include guard is retained as a positive control, preventing enforcement of `#pragma once` specifically.
