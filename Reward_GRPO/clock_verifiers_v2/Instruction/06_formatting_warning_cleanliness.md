# C06 instruction: exact formatting and warning cleanliness

## Observed failure

Trials a2 and a5 used `char[6]` plus `snprintf`, triggering `-Werror=format-truncation`. Trial a4 emitted `8:0` and `10:3`; a8 retained the same unpadded pattern.

## Contract

Formatting must compile without warnings and return exactly five characters in `HH:MM` form for every canonical time. Converting a `const clock` repeatedly must be stable and side-effect free.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C06-A | Implementation compiles under all strict warning flags |
| C06-B | Boundary values render exactly: `00:00`, `08:03`, `23:59`, `04:43` |
| C06-C | Repeated conversion of a const object is identical and length five |

No particular formatter library or private representation is required.
