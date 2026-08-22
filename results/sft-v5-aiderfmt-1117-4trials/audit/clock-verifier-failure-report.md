# Phase 1: Clock SFT Failures and Verifier Coverage Audit

This report is scoped only to the Aider Polyglot `clock` task in the four SFT-v5 trials and to the five Clock verifiers added on branch `tirtha-env-stable-midband-RL-v2`. It traces each model attempt from the injected task contract through compiler or test feedback, the attempted repair, and the terminal outcome.

Clock scores **0/4 Pass@1 and 0/4 Pass@2**: all eight attempts fail, and every final candidate stops at compilation. The terminal verifier pack is sound because mandatory Policy 3 rejects incomplete APIs, but a controlled replay exposes a shaping gap: Policies 1 and 5 do not check the required free `operator!=`, so a candidate missing only that operator passes 12 of the 15 non-aggregated policy kernels before Policy 3 rejects it.

## Primary evidence table

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| Clock SFT outcome | Establishes the task-specific denominator | **Verified:** 4 trajectories, 8 attempts, Pass@1 0/4, Pass@2 0/4, and no feedback recovery | Inspect `clock` in `audit/failure-inventory.json`; extract each trial's `responses.tar.gz` and inspect `tasks/clock/.aider.chat.history.md` | Keep this report separate from the 26-task `phase1-failure-report.md` |
| Exact task contract | Defines required API and behavior | **Verified:** `clock::at`, mutating `plus`/`minus`, implicit string conversion, `operator==`, and free `operator!=`; output is zero-padded `HH:MM`, with positive and negative modulo-day wrapping | Read overlay lines 199-218 and compare with the pinned Polyglot reference and tests | `reproduction/aider_fixed26_contract_overlay.py`; Polyglot commit `7e0611e...` |
| Terminal model failures | Observable final symptom | **4/4 compile failures:** two fixed-buffer `snprintf` warning failures, one missing `<iomanip>` plus invalid `lhs`, and one missing free `operator!=` | Read the final compiler block in each archived Clock chat | Train minimal compiler-feedback repairs under the exact C++17 warning policy |
| Repair behavior | Tests whether feedback fixes the first candidate | **0/4 recoveries.** Two repairs introduce a different API/build failure; two converge on the same `snprintf` truncation warning | Compare first and second candidate plus the intervening compiler/test feedback | Add failure-conditioned `.h`/`.cpp` repair examples and compile after each narrow edit |
| Operational overlap | Separates infrastructure symptoms from model correctness | **1 error output, 1 context exhaustion, 0 malformed responses, 0 timeouts**; both flags belong to trial a4 and are not additional trajectories | Inspect a4's source receipt and archived response | Reduce retry-context growth, but do not count these flags as exclusive failures |
| Verifier reference replay | Establishes that all five verifier policies accept a valid implementation | **Fresh local result:** reference solution passes **15/15 kernels** across CL-E01 through CL-E05 | Install pinned `.meta/example.h/.cpp` as the candidate, apply the Clock overlay, then run all five verifier scripts | Matches `Reward_GRPO/Clock Verifiers/VALIDATION_REPORT.md` |
| Missing-`!=` controlled mutant | Tests exact-API coverage independently of the failed SFT outputs | **Fresh local result:** CL-E01, E02, E04, and E05 pass 3/3 each; CL-E03 fails at the official-suite compile step and blocks its final kernel | Delete only the reference header's free `operator!=`, then run all five policies | Terminal gate remains correct; partial shaping gives 12 passing kernels to an API-incomplete candidate |
| Exact-API shaping gap | A verifier claim and implementation do not fully align | **Verified:** CL-E01 and CL-E05 probe `at`, `plus`, `minus`, conversion, and equality, but neither compiles or links a call to free `operator!=` | Inspect `verifier_01_exact_api_compile_link.py` and `verifier_05_factory_observer_odr.py` | Add a type/signature check and a real cross-translation-unit `operator!=` call |

## Scope and controls

- Audited branch: `tirtha-env-stable-midband-RL-v2` at `0a96357266da5a093b770ba963d1e7a4e6c07a1b`.
- Evaluation pins: Aider `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`; Polyglot `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`.
- Compiler contract used by the verifier executor: C++17 with `-Wall -Wextra -Wpedantic -Werror`.
- Audited SFT artifacts: `trials/{a2,a4,a5,a8}/source_run_receipt.json` and the corresponding `responses.tar.gz` archives.
- The full 26-task findings remain in `audit/phase1-failure-report.md`; this document does not revise their aggregate counts.

The prompt contract is consistent with the pinned Clock reference and tests. Unlike the separate `all-your-base` issue in the full audit, no prompt/test contradiction was found for Clock, so these failures are usable model and repair-loop evidence.

## Clock run metrics

| Trial | Attempt outcomes | Prompt tokens | Completion tokens | Duration | Operational flags | Terminal symptom |
| --- | --- | ---: | ---: | ---: | --- | --- |
| a2 | fail -> fail | 44,234 | 4,682 | 89.4 s | None | Compile: `snprintf` format-truncation warning promoted to error |
| a4 | fail -> fail | 147,919 | 2,472 | 400.8 s | 1 error output; 1 context exhaustion | Compile: missing `<iomanip>` manipulators and invalid `lhs` in member `operator!=` |
| a5 | fail -> fail | 29,201 | 1,977 | 38.5 s | None | Compile: `snprintf` format-truncation warning promoted to error |
| a8 | fail -> fail | 36,198 | 3,063 | 77.7 s | None | Compile: required free `operator!=` is undeclared |
| **Total** | **0/4 Pass@1; 0/4 Pass@2** | **257,552** | **12,194** | **606.5 s** | **1 error; 1 context; 0 malformed; 0 timeout** | **4/4 terminal compile failures** |

Trial a4 alone consumes 57.4% of Clock prompt tokens and runs for about 6.7 minutes. This supports a retry-context-growth concern, but it does not explain the other three failures and is not evidence of a test timeout.

## Attempt-by-attempt failure timeline

| Trial | First attempt | Feedback and repair | Terminal result | Root-cause reading |
| --- | --- | --- | --- | --- |
| a2 | Uses C++20 defaulted spaceship comparison (`operator<=>`) under the required C++17 toolchain, so compilation fails | Replaces it with a header-only implementation and a fixed `char[6]` plus `snprintf` formatter | `-Wformat-truncation` is fatal under `-Werror` | Language-version mismatch followed by warning-unsafe repair. The new normalization also has a latent exact-negative-day bug described below |
| a4 | Builds after a context/output-limit event but fails official behavior: `08:00` becomes `8:0` and `10:03` becomes `10:3` | Adds `std::setw`/`std::setfill`, omits `<iomanip>`, and rewrites free `operator!=` as a malformed member referring to undefined `lhs` | Compiler rejects the manipulators and `lhs` | A semantic formatting failure regresses into an include/API compile failure during repair |
| a5 | Header and source drift: the source defines constructors and uses `_minute` that the header does not declare | Adds the missing declarations and storage, but formats through a fixed six-byte `snprintf` buffer | `-Wformat-truncation` is fatal under `-Werror` | Interface repair succeeds partially, then warning cleanliness becomes the blocker |
| a8 | Defines free `operator!=` in both header and source | Removes the duplicate definition but also removes the public declaration from the header | Official tests cannot resolve `Clock != Clock` | An ODR/linkage failure regresses into an incomplete public API; unpadded `to_string` formatting also remains latent |

The a2 second attempt normalizes a negative total using a special-case formula that maps exact negative day multiples such as `-1440` or `-2880` to 1440 rather than 0. If its formatter compiled, it could emit `24:00`; CL-E04 explicitly contains whole-day and negative-input checks designed to reject this behavior. This is a code-level inference because compilation prevents that candidate from reaching the semantic kernel.

## Root-cause taxonomy

These families overlap: one attempt can violate the API, fail compilation, and contain a latent arithmetic error simultaneously. They therefore must not be added as mutually exclusive counts.

| Root-cause family | Direct Clock evidence | Trials | Training implication |
| --- | --- | --- | --- |
| C++ language/toolchain contract | C++20 spaceship emitted for a C++17 build | a2 | Include contrastive C++17 repairs and require a local strict compile before semantic edits |
| Header/source and exact public API | Undeclared constructors/member, malformed member `!=`, and deleted free-operator declaration | a4, a5, a8 | Train paired header/source edits with signature inventory checks |
| ODR and linkage | Free `operator!=` is defined in both header and source | a8 first attempt | Teach declaration vs inline definition vs one source definition explicitly |
| Formatting and warning cleanliness | Missing zero padding, missing `<iomanip>`, and fixed `snprintf` buffer warnings | a2, a4, a5, a8 latent | Prefer `ostringstream` plus `<iomanip>`; compile with the evaluator's full warning flags |
| Canonical modulo-day arithmetic | Exact negative multiples can normalize to minute 1440 | a2 latent | Teach canonical `((x % 1440) + 1440) % 1440` or an equivalent proven normalization |
| Feedback-loop discipline | No second-turn recovery; a4 and a8 replace one failure with a new one | all four | Use minimal diagnostic-led patches and re-check every required signature after repair |

The dominant pattern is not an inability to understand clock arithmetic alone. It is failure to preserve an exact, buildable C++ interface while repairing formatting or linkage errors.

## Verifier-policy coverage against observed failures

| Policy | Intended control | Which Clock failures it covers | Verified result and limitation |
| --- | --- | --- | --- |
| CL-E01: Exact API, compile, link | Three compile/link kernels for signatures and basic behavior | C++17 failure, missing includes, header/source drift, duplicate definitions, warning errors | Reference 3/3; missing-`!=` mutant also 3/3. It does not actually probe the required free `operator!=` |
| CL-E02: Semantic boundaries | Normalization, arithmetic, formatting/equality | a4/a8 zero-padding, ordinary wrap and arithmetic errors | Reference 3/3; missing-`!=` mutant 3/3. Appropriate for behavior, but it cannot replace an exact-API probe |
| CL-E03: Official functional behavior | Authenticated full official suite; mandatory terminal policy | All observable and latent deviations covered by official tests, including missing `operator!=` | Reference 3/3. Missing-`!=` mutant: asset-authentication passes, official compilation fails, and the final kernel is blocked; this preserves terminal correctness |
| CL-E04: Canonical time arithmetic | Whole-day identity, negative factory input, large signed deltas | Specifically catches a2's latent `24:00`/negative-day defect | Reference 3/3; missing-`!=` mutant 3/3 |
| CL-E05: Factory, observer, ODR | API shape, const observer, independent instances, cross-TU behavior | ODR duplication, conversion behavior, factory independence | Reference 3/3; missing-`!=` mutant also 3/3. Its API-shape checks omit free `operator!=` |

### Controlled verifier replay

| Candidate | CL-E01 | CL-E02 | CL-E03 | CL-E04 | CL-E05 | Interpretation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Pinned reference solution | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | Valid implementation accepted by all 15 kernels |
| Reference minus only free `operator!=` | 3/3 | 3/3 | 1 pass, 1 fail, 1 blocked | 3/3 | 3/3 | Terminal suite rejects it, but four shaping policies award 12 successful kernels |

The replay used the branch's own shared executor and strict compiler flags after applying the same Clock contract overlay used by the SFT evaluation. It independently agrees with the committed validation report for the unmodified reference. The missing-`!=` mutant is an additional targeted audit case, not one of the validation report's original mutants.

## Verifier root cause and recommended patch

The verifier defect is narrow: the written CL-E01 and CL-E05 policies describe the exact public contract, but their generated probes cover `at`, `plus`, `minus`, string conversion, and `operator==` without using free `operator!=`. Policy 3 prevents a false terminal success, so this is a **reward-shaping coverage gap**, not a terminal false accept.

Recommended verifier changes:

1. In CL-E01, add a compile-time expression check for `const Clock& != const Clock&` returning `bool`, and add a real linked call from a separate translation unit.
2. In CL-E05, add a free-operator use to the API-shape or ODR kernel so deletion and duplicate-definition variants are distinguished.
3. Add the controlled missing-`!=` candidate as a permanent semantic mutant and require CL-E01 and CL-E05 to reject it after the patch.
4. Preserve CL-E03 as mandatory and preserve its current evaluator-fault handling; it is the control that currently prevents terminal false acceptance.

No verifier source was changed during this Phase 1 audit. The recommendation is intentionally separated from evidence so it can be reviewed before implementation.

## Clock-specific SFT actions

1. Add one exact-API row that inventories every Clock declaration before editing either file, including the free `operator!=`.
2. Add paired repairs for three observed transitions: spaceship-to-C++17 comparison, duplicate-to-single free-operator definition, and missing header/source member declarations.
3. Add strict-build examples where `-Werror` rejects an otherwise plausible fixed-size formatter; use `ostringstream`, `setw`, and `setfill` with the correct headers.
4. Add contrastive modulo cases for `-1`, `-60`, `-1439`, `-1440`, `-1441`, and large signed minute deltas.
5. Gate each generated repair on exact signature checks, strict compilation, zero-padded formatting, and then the official suite, in that order.
6. Re-run Clock over matched seeds and report both first-attempt success and feedback recovery; the immediate target is not merely a higher token budget but at least one stable repair path.

## Directly verified facts

- All four archived Clock trajectories have `[false, false]` outcomes and terminal compile failures.
- The four trajectories use 257,552 prompt tokens, 12,194 completion tokens, and about 606.5 seconds in total.
- The injected Clock contract matches the required API and the pinned reference/test behavior, including zero-padding and modulo-day wrapping.
- The shared verifier executor uses C++17 plus strict warnings promoted to errors and authenticates pinned assets before the official-suite stage.
- A fresh reference replay passes all 15 policy kernels.
- A fresh mutant missing only free `operator!=` passes CL-E01, E02, E04, and E05, while mandatory CL-E03 rejects it during official-suite compilation.

## Inferences and boundaries

- The high a4 token count is consistent with repair-loop/context growth, but it does not establish that context exhaustion caused the invalid API edit.
- The a2 `24:00` result is inferred from its submitted normalization code; compilation stopped before a runtime assertion could demonstrate it.
- Root-cause families overlap and should not be treated as a partition of the four trajectories.
- The controlled mutant proves a missing-operator coverage gap. It does not measure how often policy-level shaping rewards cause that error during training.
- No GPU/model rerun was performed, so the effect of the proposed training rows and verifier amendments remains unverified.
- The committed validation report marks the verifier pack ready, but live reward-worker integration and throughput are outside its verified scope and remain outside this audit.

## Evidence map

- SFT aggregate and per-task inventory: `results/sft-v5-aiderfmt-1117-4trials/audit/failure-inventory.json`
- Archived Clock conversations: `results/sft-v5-aiderfmt-1117-4trials/trials/{a2,a4,a5,a8}/responses.tar.gz`
- Trial token and operational receipts: `results/sft-v5-aiderfmt-1117-4trials/trials/{a2,a4,a5,a8}/source_run_receipt.json`
- Injected Clock contract: `results/sft-v5-aiderfmt-1117-4trials/reproduction/aider_fixed26_contract_overlay.py`
- Verifier validation summary: `Reward_GRPO/Clock Verifiers/VALIDATION_REPORT.md`
- Verifier policy specifications: `Reward_GRPO/Clock Verifiers/Verifier implementation policy/`
- Executable verifier probes: `Reward_GRPO/Clock Verifiers/verifiers/`
- Shared strict compiler/authentication control: `Reward_GRPO/_shared/strange_cpp.py`

## Conclusion

For Clock, SFT-v5 has a complete failure pattern—zero first-turn passes and zero repair recoveries—driven mainly by exact-interface, C++ build, formatting, and repair-regression errors. The verifier's mandatory official-suite policy correctly prevents terminal false acceptance, but its partial reward surface should be tightened so a candidate missing required `operator!=` cannot collect 12 successful shaping kernels before being rejected.
