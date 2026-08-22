# C07 instruction: canonical normalization and arithmetic

## Observed failure

The a2 repair changed a correct modulo expression to a formula that maps exact negative day multiples to 1440, permitting `24:00`. Other candidates did not reach enough tests for a semantic verdict.

## Contract

Construction, addition, and subtraction must map arbitrary signed hour/minute totals into one canonical day. Equality is defined on normalized time, not raw inputs.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C07-A | Whole-day and exact negative-day inputs normalize to midnight |
| C07-B | Large signed `plus` and `minus` operations wrap correctly |
| C07-C | Differently expressed equivalent times compare equal; adjacent times do not |

The policy uses only public API calls and does not require the reference normalization algorithm.
