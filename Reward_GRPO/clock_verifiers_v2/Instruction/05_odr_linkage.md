# C05 instruction: ODR-safe linkage

## Observed failure

Trial a8 defined namespace-scope `operator!=` in multiple translation units, then over-corrected by deleting the declaration.

## Contract

`clock.h` must be safely includable more than once and from multiple translation units. All required symbols must have exactly one link-valid definition under the candidate's chosen legal strategy.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C05-A | Repeated header inclusion in one translation unit compiles |
| C05-B | Two callers plus `clock.cpp` link without duplicate/missing symbols |
| C05-C | `operator!=` is called from a different translation unit and returns the correct value |

This is a build/link policy; source-text guesses about `inline` are not used.
