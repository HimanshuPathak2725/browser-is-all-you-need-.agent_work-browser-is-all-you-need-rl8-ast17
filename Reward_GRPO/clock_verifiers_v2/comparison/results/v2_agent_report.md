# Clock Version 2 verifier agent report

Testing agent B independently ran only the custom Version 2 aggregate runner and its CL2-C01–CL2-C08 policies against the frozen canonical baseline, the dataset's official-pass control, and all 14 intentionally faulty candidates. Every candidate was reconstructed from the pinned Clock fixture with only `clock.h` and `clock.cpp` overlaid, and every run used a new output directory.

The corrected clean run detected 14/14 targeted faults, including 11/14 through the official terminal policy and 13/14 through shaping policies. The canonical baseline passed all eight policies, all 16 candidates produced valid receipts, and no INVALID result occurred.

## Candidate evidence

| Candidate | Kind | CL2-C08 terminal | C01–C07 shaping | Failed policy IDs |
|---|---|---:|---:|---|
| `canonical_baseline` | Baseline | PASS | No | — |
| `a01-clock-turn2` | Dataset official-pass control | PASS | Yes | C02, C03, C05, C07 |
| `f01_cxx20_spaceship` | Fault | FAIL | Yes | C01–C08 |
| `f02_missing_iomanip` | Fault | FAIL | Yes | C01–C08 |
| `f03_missing_inequality` | Fault | FAIL | Yes | C03, C04, C05, C07, C08 |
| `f04_missing_constructor_declaration` | Fault | FAIL | Yes | C01–C08 |
| `f05_noninline_header_operator` | Fault | FAIL | Yes | C01–C08 |
| `f06_snprintf_warning` | Fault | FAIL | Yes | C01–C08 |
| `f07_unpadded_format` | Fault | FAIL | Yes | C06, C07, C08 |
| `f08_negative_whole_day` | Fault | FAIL | Yes | C07, C08 |
| `f09_plus_off_by_one` | Fault | FAIL | Yes | C07, C08 |
| `f10_minus_noop` | Fault | PASS | Yes | C07 |
| `f11_equality_ignores_minutes` | Fault | FAIL | Yes | C07, C08 |
| `f12_official_rare_case` | Fault | FAIL | No | C08 |
| `f13_missing_default_argument` | Fault | PASS | Yes | C02, C03, C05 |
| `f14_member_instead_of_free_inequality` | Fault | PASS | Yes | C03 |

## Coverage facts

- Overall targeted-fault detection: **14/14 (100%)**.
- Terminal CL2-C08 fault detection: **11/14 (78.6%)**.
- Shaping CL2-C01–CL2-C07 fault detection: **13/14 (92.9%)**.
- Complementarity is directly observed: F12 is terminal-only, while F10, F13, and F14 are shaping-only.
- Fault detections by policy were C01 5, C02 6, C03 8, C04 6, C05 7, C06 6, C07 11, and C08 11. These counts overlap and must not be summed.
- The dataset control passed the official terminal policy but failed the stricter Version 2 contract policies. It is excluded from the 14-fault denominator and is evidence of an official-versus-strict-contract boundary, not a fault-detection claim.

## Reproducibility and audit boundary

- Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`; expected family `13.3`.
- Pinned fixture: `/tmp/clock-verifier-audit.AjXhUg/practice/clock`.
- Fresh candidate work root: `/tmp/clock-v2-agent-comparison-work`.
- Complete receipt root: `/tmp/clock-v2-agent-comparison-receipts` (16 aggregate and 128 policy receipts).
- Frozen manifest SHA-256: `7ee634c09bbafadc2670c8aa3514de0623bddc8fae382b9f788acbf2383a6821`.
- Normalized result SHA-256: `5d3c691b825ca60acd7fc4493419a286e28ae5b645dfe668a4871c30cccd455f`.
- All candidate hashes matched the manifest before execution; all 144 recorded aggregate/policy receipt hashes were rechecked with zero mismatches.

The run establishes complete detection only for this controlled 14-mutant corpus. It does not by itself establish coverage over arbitrary unseen Clock implementations; comparison and similarity claims require the separately generated original-verifier result set.
