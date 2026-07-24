# GLM-4.7 Aider AST17 GRPO Reward Policy V2

## Verdict

Use a hybrid Aider-GRPO reward policy. The existing multi-rubric architecture is useful, but it must be adapted to Aider whole-file editing. The main goal is to create rankable rewards before full correctness, while keeping full hidden-test pass as the dominant outcome.

## Current Problems To Fix

| Current Problem | Evidence | Policy Fix |
| --- | --- | --- |
| Reward is too bucketed | The successful GRPO monitor eval collapsed all `832` rewards into `-0.50`, `-0.80`, and `-1.00`. | Add intermediate rewards for parse quality, file-label recovery, compile diagnostics, zero-pass runtime, partial tests, and full pass. |
| Compile failures are flat | `722 / 832` monitor-eval samples got `compilation_failure = -0.50`. | Split compile failures by diagnostic severity so near-compiling code outranks broken code. |
| Fatal parse failures are flat | No-file output, wrong labels, bad fences, and clarification-only answers all collapse to `fatal_parse_failure = -0.80`. | Add detailed Aider parse buckets. |
| No positive reward signal | Final monitor eval had `0 / 32` all-tests-pass and all evals had `0 / 832` pass assignments. | Add small positive reward for compile-and-run zero-pass plus stronger partial-test reward. |
| AST/style reward activates too late | `s_ast17`, `s_style`, and bloat scoring only run after `all_tests_pass`. | Add small pre-pass AST/mechanism reward after safe parsing. |
| Style is duplicate telemetry | Current code sets `s_style = s_ast17`. | Replace it with independent C++ quality checks. |
| Full pass has no hard floor | Full pass can be reduced by style/bloat formula. | Add `reward >= 0.85` for any all-tests-pass candidate. |
| Weak-signal runs can continue | Signal gate is optional through `GLM47_AIDER_REQUIRE_SIGNAL`. | Require first-rollout reward variance for full GRPO runs. |

## Reward Ladder

| Outcome | Reward | Terminal? | Notes |
| --- | ---: | --- | --- |
| Verifier infrastructure fault | mask / drop sample | yes | Do not train on broken evaluator state. |
| Forbidden file, test edit, CMake edit, path escape, verifier bypass | `-1.00` | yes | Hard floor. Never soften this. |
| Clarification-only answer or no file output | `-0.92` | yes | Worse than bad code because it cannot be evaluated. |
| Fatal parse failure with no recoverable editable file | `-0.85` | yes | Bad format, but not as severe as forbidden behavior. |
| Wrong file label or non-editable target with code present | `-0.75` | yes | Code exists, but it targets the wrong file. |
| Recoverable Aider format issue with editable code extracted | downstream shaped with format penalty | no, if safe | Rewards movement toward valid Aider file output and keeps a `recoverable_format_...` reason prefix. |
| Exact Aider file format but severe compile failure | `-0.55` | yes | Valid format should outrank bad format. |
| Compile failure: syntax error, missing include/type, API mismatch, linker issue | `-0.55` to `-0.30` | yes | Diagnostic class controls the score. |
| Compiles and runs, zero tests pass | `0.05` to `0.12` | no | Crossing compile/run boundary should become positive. |
| Partial tests pass | `0.15 + 0.60*S_tests + small bonuses`, cap `0.80` | no | Strong ordinal correctness signal. |
| Full hidden-test pass | `max(0.85, shaped_score)` | yes | Correctness must dominate all auxiliary signals. |
| Clean full pass with style, safety, and performance | `0.90` to `1.00` | yes | Best band. |

## Rubric Templates

| Task Category | Active Rubrics | Base Weights | Notes |
| --- | --- | --- | --- |
| `standard` | correctness, aider_format, compile_diagnostics, ast_mechanism, memory_safety, cpp_quality | `0.70 / 0.08 / 0.08 / 0.06 / 0.04 / 0.04` | Default Aider C++ tasks. |
| `state_concurrency` | correctness, aider_format, compile_diagnostics, state_contract, thread_safety, memory_safety, cpp_quality | `0.65 / 0.07 / 0.07 / 0.08 / 0.05 / 0.04 / 0.04` | Adds state and thread safety signal. |
| `performance_intensive` | correctness, aider_format, compile_diagnostics, runtime, memory_safety, cpp_quality | `0.68 / 0.07 / 0.07 / 0.08 / 0.04 / 0.06` | Runtime activates only after correctness is positive. |
| `format_sensitive` | correctness, aider_format, compile_diagnostics, output_contract, cpp_quality | `0.68 / 0.12 / 0.07 / 0.08 / 0.05` | For string/grid/date/output-format tasks. |

## Rubric Scoring

| Rubric | Score Range | Policy |
| --- | ---: | --- |
| `correctness` | `-0.55` to `1.00` | Full pass is `1.0`; partial pass is `0.15 + 0.60*S_tests`; compile/run zero-pass is `0.05..0.12`; compile failure is delegated to diagnostics. |
| `aider_format` | `-0.92` to `0.08` | Reward exact editable file labels, all expected files, and no extra files. Penalize no files, wrong labels, duplicate files, non-editable targets, and recoverable labels separately. |
| `compile_diagnostics` | `-0.55` to `-0.30` | Severe syntax errors score lowest; missing include/type/API mismatch score higher; small linker or warning-as-error issues score highest among compile failures. |
| `ast_mechanism` | `0.00` to `0.06` | Small pre-pass bonus for required API names, plausible C++17 structure, expected data structures, and task-specific mechanisms. |
| `memory_safety` | `-0.50` to `0.04` | ASan/UBSan failure is hard negative. Clean sanitizer adds only a small bonus after compile/run. |
| `thread_safety` | `-0.50` to `0.05` | Only for state/concurrency tasks. TSan error is negative; unavailable TSan should be neutral, not fail-closed. |
| `runtime` | reserved | Activate only after correctness is positive and after the Aider harness exposes candidate/reference runtime metrics. Never reward faster wrong code. |
| `cpp_quality` | `-0.06` to `0.06` | Use independent C++ quality checks, tightly capped so style cannot outrank correctness. |

## Final Reward Formula

| Case | Formula |
| --- | --- |
| Hard forbidden | `R = -1.00` |
| Fatal parse or no code | `R = parse_bucket` |
| Recoverable format with editable code | Continue to compile/test verification; apply lower `S_format` and prefix the final reason with `recoverable_format_`. |
| Compile failure | `R = compile_diag_bucket + aider_format_bonus + mechanism_bonus`, cap `-0.30` |
| Runs but fails all tests | `R = 0.05 + 0.07*S_format + 0.05*S_mechanism`, cap `0.12` |
| Partial pass | `R = 0.15 + 0.60*S_tests + 0.06*S_format + 0.05*S_mechanism + 0.04*S_safety + 0.03*S_cpp_quality`, cap `0.80` |
| Full pass | `R = max(0.85, 0.90 + 0.04*S_ast + 0.03*S_cpp_quality + 0.02*S_format - bloat_cap)`, clamp `1.00` |

## Compile Diagnostic Buckets

| Compile Outcome | Reward Band | Examples |
| --- | ---: | --- |
| Severe syntax parse failure | `-0.55` | Unclosed braces, invalid declarations, broken templates. |
| Missing required symbol or function | `-0.50` | Required API not implemented. |
| Missing include or unknown type | `-0.45` | `std::vector` without include, undefined helper type. |
| Signature or API mismatch | `-0.42` | Wrong return type, missing const, wrong parameter shape. |
| Linker or duplicate definition issue | `-0.38` | Multiple definitions, missing object symbol. |
| Warning-as-error or narrow local issue | `-0.35` to `-0.30` | Unused variable, signedness warning, small fix needed. |

## Aider Format Buckets

| Format Outcome | Reward |
| --- | ---: |
| Forbidden file/path/test edit | `-1.00` |
| Clarification-only or no files | `-0.92` |
| No recoverable editable file block | `-0.85` |
| Code block exists but wrong/non-editable label | `-0.75` |
| Duplicate editable file block | `-0.70` |
| Recoverable basename/path-prefixed label | downstream shaped with `recoverable_format_...` prefix |
| All editable files extracted, minor fence/language issue | downstream shaped with lower `S_format` |
| Exact Aider whole-file format | `+0.04` to `+0.08` auxiliary bonus |

## Guardrails

| Guardrail | Rule |
| --- | --- |
| Correctness dominance | Any full pass must outrank any partial pass. |
| Partial dominance | Any partial pass must outrank any compile failure. |
| Compile dominance | Near-compiling code must outrank unrecoverable parse failures. |
| Security floor | Forbidden file/runtime primitive always stays `-1.00`. |
| Auxiliary cap | Style, reasoning, AST, runtime, and format bonuses cannot push wrong code above correct code. |
| Aider format | Use Aider whole-file editable file labels, not a single generic C++ block contract. |
| Runtime safety | Runtime bonus only applies after correctness is positive. |
| Signal gate | Full GRPO runs must require first-rollout reward variance. |

## Signal Gate For Full GRPO

| Env Var | Value | Purpose |
| --- | ---: | --- |
| `GLM47_AIDER_REQUIRE_SIGNAL` | `1` | Enables the first-rollout signal gate. |
| `GLM47_AIDER_MIN_REWARD_VARIANCE_GROUPS` | `4` | Requires enough prompt groups to contain more than one reward value. |
| `GLM47_AIDER_MIN_SEMANTIC_VARIANCE_GROUPS` | `2` | Requires semantic/test-count variation in at least a few groups. |
| `GLM47_AIDER_MIN_EXACT_FORMAT_RATE` | `0.75` | Requires most samples to use exact Aider whole-file format. |
| `GLM47_AIDER_MIN_COMPILE_RATE` | `0.90` | Requires most parsed candidates to compile before committing to a full run. |

## Target Ordering

| Rank | Outcome | Meaning |
| ---: | --- | --- |
| 1 | Forbidden/bypass | Worst outcome; protected files, tests, CMake, path escape, or verifier bypass. |
| 2 | Clarification/no-file | No usable file edit was produced. |
| 3 | Fatal parse | Output cannot be safely converted into editable Aider files. |
| 4 | Recoverable Aider format | Code is present and recoverable, but formatting/file labels are not exact. |
| 5 | Compile failure graded by diagnostic | Candidate has editable files but does not compile; near-fixes score higher than severe failures. |
| 6 | Compiles and runs but zero tests | Candidate crosses the compile/run boundary but fails all checks. |
| 7 | Partial tests | Candidate passes some visible/hidden checks. |
| 8 | Full pass | Best correctness tier; all tests pass. |

## Implementation Priority

| Priority | Change |
| --- | --- |
| P0 | Add Aider parse buckets and compile diagnostic buckets. |
| P0 | Add full-pass reward floor `>= 0.85`. |
| P0 | Keep production failure rewards negative, not `0.0`, for GRPO. |
| P1 | Add pre-pass AST/mechanism scoring after safe parsing. |
| P1 | Preserve recoverable-format telemetry in reward reasons. |
| P1 | Ensure shadow graders expose useful partial assertions. |
| P1 | Enable first-rollout signal gate for full GRPO runs. |
| P2 | Replace duplicate style score with independent C++ quality checks. |
| P2 | Add task-family reward summaries to W&B and artifacts. |
