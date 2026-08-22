# Clock verifier v2 validation report

The v2 package was validated against the exact pinned Clock reference, eight one-fault category mutants, two evaluator-fault controls, and two repair-transition controls. The campaign ran the same aggregate C01-C08 path used by consumers and preserved per-policy compiler, linker, runtime, and hash receipts outside candidate source.

The campaign passed: the reference scored 24/24 kernels, every target mutant failed its intended policy, all eight mutants failed terminal C08, protected-asset tampering and a missing compiler were `INVALID`, and C09 correctly recognized recovery and regression without emitting reward. These controls establish deterministic known-case sensitivity, not production calibration or completeness against unknown mutants.

## Primary evidence table

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| Reference | Positive control | **Pass:** C01-C08 each 3/3; 24/24 total | Rerun `validation/validate.py` | Pinned `.meta/example.h/.cpp` installed as candidate |
| C01 mutant | C++20 syntax under C++17 | Target failed; C08 rejected | Inspect `c01_language_mode` receipts | Known a2 analogue |
| C02 mutant | Missing `<iomanip>` | Target failed; C08 rejected | Inspect `c02_dependency` receipts | Known a4 analogue |
| C03 mutant | Missing free `operator!=` | C01/C02/C06 passed; C03 failed; C08 rejected | Inspect matrix | Closes original shaping gap |
| C04 mutant | Missing constructor declaration | Target failed; C08 rejected | Inspect `c04_header_source` | Known a5 analogue |
| C05 mutant | Non-inline header definition | Target failed; C08 rejected | Inspect linker log | Known a8 ODR analogue |
| C06 mutant | Unpadded rendering | C01-C05 passed; C06/C07/C08 failed | Inspect matrix | Localized semantic formatting signal |
| C07 mutant | `24:00` normalization | C01-C06 passed; C07/C08 failed | Inspect matrix | Localized modulo-day signal |
| C08-only mutant | One official case changed | C01-C07 passed; only C08 failed | Inspect matrix | Proves terminal gate necessity |
| Evaluator faults | Tampered test and missing compiler | **16/16 policy outcomes INVALID**; never candidate fail/pass | Rerun fault controls | Confirms failure-domain separation |
| C09 transitions | Repair audit | FP=`recovered`, PF=`regressed`, both non-reward | Inspect transition receipts | Requires live snapshot integration next |

## Final mutation matrix

`P` is policy pass and `F` is candidate failure.

| Control | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reference | P | P | P | P | P | P | P | P |
| C01 language | F | F | F | F | F | F | F | F |
| C02 dependency | F | F | F | F | F | F | F | F |
| C03 API | P | P | F | F | F | P | F | F |
| C04 header/source | F | F | F | F | F | F | F | F |
| C05 ODR | F | F | F | F | F | F | F | F |
| C06 formatting | P | P | P | P | P | F | F | F |
| C07 semantics | P | P | P | P | P | P | F | F |
| C08 official-only | P | P | P | P | P | P | P | F |

Broad failure rows are expected when a candidate cannot compile or link: downstream semantic policies cannot execute. The matrix is a dependency surface, not a confusion matrix and not nine statistically independent observations.

## Directly verified facts

- GCC identity was 13.3.0 and the protected contract matched the pinned Polyglot hashes.
- Reference source passed all 24 reward kernels.
- Eight of eight controlled source mutants were killed by their intended policy and terminal C08; zero survived.
- Tampered official tests and the nonexistent compiler made every category `INVALID`.
- Candidate source remained outside verifier output and was guarded by before/after combined digests in each policy.
- Final raw summary SHA-256: `7e055de23d0a76405654414559d745325dbad4b552ce1a64c7d17c24f117bb0f`.

## Inferences and unverified boundaries

- The observed localization pattern supports using C01-C07 as shaping signals, but reward weights and correlations have not been calibrated on model-generated samples.
- Eight hand-designed mutants do not prove completeness against compiler, linker, undefined-behavior, or adversarial reward-hacking variants.
- Repeatability across different machines/compilers is not established; the contract intentionally rejects anything except expected GCC 13.3.
- Live reward-worker invocation, concurrency limits, wall-clock distribution, and receipt ingestion remain unverified.
- C09 is intentionally excluded from reward until immutable per-turn source snapshots are available.

## Reproduce

```bash
python3 Reward_GRPO/clock_verifiers_v2/validation/validate.py \
  --template-exercise-dir /path/to/pinned/clock \
  --output-dir /new/empty/clock-validation \
  --jobs 3
```

The final audit run wrote its external receipt tree to `/tmp/clock-v2-validation-final`; rerunning is the durable source of evidence because temporary paths are not repository artifacts.

## Conclusion

The package is implementation-complete for local deterministic validation and has concrete evidence for positive acceptance, targeted fault rejection, terminal gating, evaluator invalidation, and repair-transition labeling. The remaining risk is production reward calibration, so the next concrete step is a shadow GRPO run that records C01-C09 without using the new signals for optimization.
