# Unified final Kindergarten Garden verifiers

This package consolidates Kindergarten Garden build, API, roster, row-geometry, full-domain, safety, and official-suite checks into six independently executable policies. C01-C05 provide focused contract signals; C06 authenticates and executes the complete pinned official suite.

The aggregate runner defaults to `strict` acceptance because the contract includes exact enum/API shape, dependency integrity, all supported garden widths, bounded `string_view` behavior, and integration safety that the 17 official examples do not fully observe. `official` remains available as a narrower diagnostic compatibility mode.

| Policy | Boundary | Kernels |
| --- | --- | ---: |
| KGF-C01 | C++17 build, strict warnings, external link, protected-dependency isolation | 4 |
| KGF-C02 | Exact enum/function API, repeated include, multi-TU integration | 3 |
| KGF-C03 | Complete roster mapping, bounded views, and repeatability | 2 |
| KGF-C04 | Dynamic row widths and exact cup order | 2 |
| KGF-C05 | Generated oracle, interleaving, and runtime safety | 2 |
| KGF-C06 | Protected-asset authentication and complete official suite | 3 |

Run the default strict reward boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/kindergarten-garden \
  --output-dir /new/empty/output
```

Run the narrower official-only compatibility boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/kindergarten-garden \
  --output-dir /new/empty/output \
  --acceptance-mode official
```

The aggregate receipt reports `official_success`, `shaping_success`, `strict_contract_success`, selected `reward_ready`, per-policy receipt hashes, and cross-policy source consistency. `INVALID` represents an evaluator, tool, or protected-asset failure and never a candidate rejection.
