# CLF-C06 implementation report

`verifier_06_official_terminal.py` preserves the shared authenticated official executor used by original CL-E03 and v2 CL2-C08. This is intentionally not replaced by selected property checks: a targeted `(201, 3001)` mutant proved that partial policies can all pass while an official case fails.

Protected-asset or compiler faults produce `INVALID`; candidate compile, link, assertion, or runtime failures produce `FAIL`. The aggregate exposes C06 separately as `official_success` and never derives it from shaping scores.
