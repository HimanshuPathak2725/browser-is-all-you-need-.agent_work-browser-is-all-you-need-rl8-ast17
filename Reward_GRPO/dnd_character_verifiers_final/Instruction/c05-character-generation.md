# DNF-C05: character generation

Construct 5,000 characters under runtime-safety instrumentation. Every stored ability must remain in `[3,18]`, and every character must satisfy `hitpoints == 10 + modifier(constitution)`.

A second kernel checks that the constructor actually performs six ability generations instead of copying or hard-coding fields. No more than 5% of characters may have all six abilities equal. Each field position must observe at least 13 distinct values and a mean between `11.5` and `13.0`, broad bounds around the exact four-dice/drop-lowest distribution.

Invariant, independence, distribution, or safety violations are `FAIL`. Evaluator failures are `INVALID`.
