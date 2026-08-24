# Unified final Crypto Square verifiers

This package consolidates Crypto Square build, API, normalization, segmentation, full-domain, safety, and official-suite checks into six independently executable policies. C01-C05 provide focused contract signals; C06 authenticates and executes the complete pinned official suite.

The aggregate runner defaults to `strict` acceptance because the complete Crypto Square contract includes dependency integrity, exact API integration, broad length boundaries, and state safety that the eight official examples do not fully observe. `official` remains available as a narrower diagnostic compatibility mode.

| Policy | Boundary | Kernels |
| --- | --- | ---: |
| CSF-C01 | C++17 build, strict warnings, external link, protected-dependency isolation | 4 |
| CSF-C02 | Exact public method types, repeated include, multi-TU integration | 3 |
| CSF-C03 | ASCII normalization, source isolation, and size boundaries | 2 |
| CSF-C04 | Plaintext segmentation and rectangle relations | 2 |
| CSF-C05 | Full-domain oracle, repeatability, copying, and runtime safety | 2 |
| CSF-C06 | Protected-asset authentication and complete official suite | 3 |

Run the default strict reward boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/crypto-square \
  --output-dir /new/empty/output
```

Run the narrower official-only compatibility boundary:

```bash
python3 verifiers/run_all.py \
  --exercise-dir /path/to/crypto-square \
  --output-dir /new/empty/output \
  --acceptance-mode official
```

The aggregate receipt reports `official_success`, `shaping_success`, `strict_contract_success`, selected `reward_ready`, per-policy receipt hashes, and cross-policy source consistency. `INVALID` represents an evaluator, tool, or protected-asset failure and never a candidate rejection.
