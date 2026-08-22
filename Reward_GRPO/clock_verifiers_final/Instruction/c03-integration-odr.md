# CLF-C03 instruction: integration, ODR, and state isolation

## Contract

The header must tolerate repeated inclusion and multiple translation units. Public symbols must have one link-valid definition, the free inequality operator must resolve across translation units, factories must produce independent values, and const observation must not mutate state.

| Kernel | Pass condition |
| --- | --- |
| C03-A | The header can be included twice in one translation unit |
| C03-B | Two external translation units plus `clock.cpp` link and exercise formatting/inequality |
| C03-C | Independent factory values and repeated const observation preserve state |

The policy uses compiler, linker, and black-box runtime evidence; it never searches source text for `inline` or private field names.
