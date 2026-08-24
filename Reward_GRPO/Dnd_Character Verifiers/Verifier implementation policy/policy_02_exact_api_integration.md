# DNF-C02 policy: exact API and integration

Require the public interface stated by the pinned task: `int modifier(int)`, `int ability()`, a default-constructible `Character`, and seven public `int` data members with the exact required names.

The policy compiles exact type assertions, executes the callable surface through function pointers, and links two independent translation units after including the header twice. Header-only solutions are accepted when their definitions are correctly `inline` or in-class; non-inline header definitions fail the ODR integration kernel.

API, include, compile, link, or observable contract mismatches are `FAIL`. Evaluator failures remain `INVALID`.

## Implementation rationale

The type probe uses function-pointer and pointer-to-data-member assertions. This distinguishes the required public fields from similarly named methods and rejects wrong return/member types without constraining private implementation choices.

The integration kernel includes the header twice in one translation unit and consumes it from two translation units plus `dnd_character.cpp`. This directly reproduces the iter-19 repair endpoint that moved non-inline definitions into the header and failed at link time, while accepting correctly inline header-only alternatives.
