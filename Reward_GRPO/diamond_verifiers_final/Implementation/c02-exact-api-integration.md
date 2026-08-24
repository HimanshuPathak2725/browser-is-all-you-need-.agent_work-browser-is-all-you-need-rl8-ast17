# DMF-C02 implementation report

`verifier_02_exact_api_integration.py` combines original Policy 3's exact function type with repeated-include and multi-translation-unit integration checks. C02-A uses `decltype(&diamond::rows)` so a callable but incorrect `int` parameter cannot pass through implicit conversion.

C02-B and C02-C use compiler/linker evidence instead of source heuristics. Validation specifically retained a legal declaration-only header without `#pragma once` as a positive control, preventing the policy from confusing one guard style with include idempotence.
