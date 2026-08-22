# Unified final Clock verifiers

This package consolidates the strongest original and Version 2 checks into six independently executable policies. C01-C05 are granular shaping/diagnostic policies; C06 authenticates and executes the complete pinned official suite.

The aggregate runner exposes two explicit reward contracts. `official` is the default and accepts any candidate that passes authenticated official tests, while still recording strict failures. `strict` requires the canonical public API and every shaping policy in addition to official success.

| Policy | Boundary | Kernels |
| --- | --- | ---: |
| CLF-C01 | C++17, header/dependencies, strict implementation build, external link | 3 |
| CLF-C02 | Exact public API, default call surface, member types, free inequality | 3 |
| CLF-C03 | Include idempotence, multi-TU ODR/linkage, object-state isolation | 3 |
| CLF-C04 | All 1,440 canonical formats, signed boundaries, const observer stability | 3 |
| CLF-C05 | Construction/arithmetic/relation property sweeps under UBSan | 3 |
| CLF-C06 | Protected-asset authentication and complete official terminal suite | 3 |

Run with official correctness as the reward boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/clock \
  --output-dir /new/empty/output
```

Run with exact canonical conformance:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/clock \
  --output-dir /new/empty/output \
  --acceptance-mode strict
```

The aggregate receipt reports `official_success`, `shaping_success`, `strict_contract_success`, selected `reward_ready`, per-policy receipt hashes, and cross-policy source consistency. `INVALID` represents evaluator/tool/asset failure and never candidate rejection.
