# CLF-C03 policy: integration, ODR, and state isolation

## Contract

The header must tolerate repeated inclusion and multiple translation units. Public symbols must have one link-valid definition, the free inequality operator must resolve across translation units, factories must produce independent values, and const observation must not mutate state.

| Kernel | Pass condition |
| --- | --- |
| C03-A | The header can be included twice in one translation unit |
| C03-B | Two external translation units plus `clock.cpp` link and exercise formatting/inequality |
| C03-C | Independent factory values and repeated const observation preserve state |

The policy uses compiler, linker, and black-box runtime evidence; it never searches source text for `inline` or private field names.

## Implementation rationale

`verifier_03_integration_odr.py` combines v2's repeated-include and multi-TU probes with original E05's factory/observer independence checks. The multi-TU executable calls both string conversion and free inequality from a helper translation unit, catching duplicate and missing symbols under normal linker rules.

Source-text heuristics are excluded. A legal out-of-line or inline implementation passes if compiler/linker behavior and runtime state isolation are correct.
