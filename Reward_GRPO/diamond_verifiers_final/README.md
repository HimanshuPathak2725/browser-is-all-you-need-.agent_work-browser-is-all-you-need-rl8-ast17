# Unified final Diamond verifiers

This package consolidates the Diamond build, API, integration, geometry, full-domain, safety, and official-suite checks into six independently executable policies. C01-C05 provide focused contract signals; C06 authenticates and executes the complete pinned official suite.

The aggregate runner defaults to `strict` acceptance because the Diamond contract includes exact API/dependency integrity and A-Z behavior that the five official examples do not fully observe. `official` remains available as a narrower diagnostic compatibility mode.

| Policy | Boundary | Kernels |
| --- | --- | ---: |
| DMF-C01 | C++17 build, strict warnings, external link, protected-dependency isolation | 4 |
| DMF-C02 | Exact `rows(char)` API, repeated include, multi-TU linkage | 3 |
| DMF-C03 | A-Z square dimensions, determinism, and state isolation | 2 |
| DMF-C04 | Glyph placement, spacing, symmetry, and letter order | 2 |
| DMF-C05 | Full A-Z byte oracle and interleaved repeats under safety checks | 2 |
| DMF-C06 | Protected-asset authentication and complete official suite | 3 |

Run the default strict reward boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/diamond \
  --output-dir /new/empty/output
```

Run the narrower official-only compatibility boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/diamond \
  --output-dir /new/empty/output \
  --acceptance-mode official
```

The aggregate receipt reports `official_success`, `shaping_success`, `strict_contract_success`, selected `reward_ready`, per-policy receipt hashes, and cross-policy source consistency. `INVALID` represents an evaluator, tool, or protected-asset failure and never a candidate rejection.
