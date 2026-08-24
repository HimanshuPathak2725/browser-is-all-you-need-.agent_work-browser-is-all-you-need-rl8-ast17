# Unified final D&D Character verifiers

This package consolidates D&D Character build, exact API, modifier, dice-generation, character-state, safety, and official-suite checks into six independently executable policies. DNF-C01 through DNF-C05 provide focused reward signals; DNF-C06 authenticates and executes the complete pinned official suite.

The aggregate runner defaults to `strict` acceptance. This is intentional: the official suite checks only that generated abilities fall in `[3, 18]`, so constant, uniform, three-dice, and correlated generators can pass it. `official` remains available as a compatibility diagnostic.

| Policy | Boundary | Kernels |
| --- | --- | ---: |
| DNF-C01 | C++17 build, strict warnings, external link, protected-dependency isolation | 4 |
| DNF-C02 | Exact function/member API, repeated include, and multi-TU ODR integration | 3 |
| DNF-C03 | Complete modifier table and mathematical floor semantics | 2 |
| DNF-C04 | Ability support and fair four-dice/drop-lowest distribution | 2 |
| DNF-C05 | Six character rolls, field distributions, hit-point derivation, and runtime safety | 2 |
| DNF-C06 | Protected-asset authentication and complete official suite | 3 |

Run the default strict boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/dnd-character \
  --output-dir /new/empty/output
```

Run the official-only compatibility boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/dnd-character \
  --output-dir /new/empty/output \
  --acceptance-mode official
```

The aggregate receipt reports `official_success`, `shaping_success`, `strict_contract_success`, selected `reward_ready`, per-policy receipt hashes, and cross-policy source consistency. `INVALID` represents an evaluator, tool, or protected-asset failure and never a candidate rejection.
