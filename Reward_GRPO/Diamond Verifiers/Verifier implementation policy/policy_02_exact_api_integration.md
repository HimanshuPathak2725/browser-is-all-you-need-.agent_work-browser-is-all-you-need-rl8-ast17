# DMF-C02 policy: exact API and integration

## Contract

Strict conformance requires the exact free-function type `std::vector<std::string> diamond::rows(char)`. The header must tolerate repeated inclusion, and the public symbol must compile, link, and execute across multiple translation units.

| Kernel | Pass condition |
| --- | --- |
| C02-A | `decltype(&diamond::rows)` exactly matches `std::vector<std::string> (*)(char)` |
| C02-B | Including `diamond.h` twice in one translation unit compiles |
| C02-C | Two external translation units plus `diamond.cpp` link and call the API |

The policy checks compiler and linker behavior rather than requiring `#pragma once`, a named guard, `inline`, or any particular source layout.

## Implementation rationale

`verifier_02_exact_api_integration.py` combines original Policy 3's exact function type with repeated-include and multi-translation-unit integration checks. C02-A uses `decltype(&diamond::rows)` so a callable but incorrect `int` parameter cannot pass through implicit conversion.

C02-B and C02-C use compiler/linker evidence instead of source heuristics. Validation specifically retained a legal declaration-only header without `#pragma once` as a positive control, preventing the policy from confusing one guard style with include idempotence.
