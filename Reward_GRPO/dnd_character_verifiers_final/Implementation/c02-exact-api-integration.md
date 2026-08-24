# Implementing DNF-C02

The type probe uses function-pointer and pointer-to-data-member assertions. This distinguishes the required public fields from similarly named methods and rejects wrong return/member types without constraining private implementation choices.

The integration kernel includes the header twice in one translation unit and consumes it from two translation units plus `dnd_character.cpp`. This directly reproduces the iter-19 repair endpoint that moved non-inline definitions into the header and failed at link time, while accepting correctly inline header-only alternatives.
