# R6 GRPO policy, reward, diagnostics, and execution audit

Audit date: 2026-08-12
Repository revision: `19c68240991563e4ddbc0171485b1850101e7e2b` plus a dirty working tree
Audited experiment: `unadmitted-r6-v2-four-topic40-20260812T045951Z`
Audited checkpoint: `iter_0000005`

## Executive decision

The current R6 system is a successful **engineering experiment**, not an admitted
training or promotion candidate. Hybrid45 V2, the isolated C++17 verifier, the
fail-closed infrastructure behavior, group size eight, conservative learning
rate, gradient clipping, and the reduced response/token-pack limits are supported
by implementation tests and stored execution evidence.

The complete 475-task run is still blocked. It has not completed one optimizer
update because of duplicate task groups and a verifier infrastructure failure on
a concurrency task. The successful 40-task run completed six optimizer updates,
but it bypassed a failed smoke gate, disabled within-batch task uniqueness, used a
non-concurrent subset, and remains explicitly `QUARANTINE_ONLY`.

| Area | Evidence-backed result | Formal disposition |
| --- | --- | --- |
| Hybrid45 V2 arithmetic and receipts | Exact endpoints, weights, observation masks, overrides, and tamper checks pass | Justified |
| Whole-file response contract | Correct contract for this repository; 592/960 training rollouts were exact-format | Justified contract, insufficient reliability |
| C++ verification | GCC 13/C++17, API/type, warning, link, runtime, five hidden partitions, sanitizer, and repeatability surfaces exist | Justified; full concurrency path unresolved |
| GRPO numerical behavior | Six finite updates; gradient norm 0.1167–0.1614; no clipping or NaN | Stable over six updates only |
| Memory profile | R3/R4 OOM; R5 passed at 69,385 MiB; R6 peaked at 73,339 MiB | Current 16,384/18,432 limits justified |
| Rollout diversity | Reward variance in 117/120 groups and kernel variance in 118/120 groups | Strong signal |
| Task sampling | Every successful batch contained duplicate task groups, although every task received exactly three total exposures | Needs sampler fix |
| Length behavior | Training truncation 7.5–15.0%, 108/960 overall; development truncation rose from 4/60 to 5/60 | Needs update |
| Full-corpus execution | First attempt rejected duplicate groups; retry aborted on verifier infrastructure failure | Not completed |
| Clean fixed-26 evaluation | Pass@1 0/26; Pass@2 6/26; 26/26 well formed; 11 context exhaustions | Mixed, not promotion evidence |
| Admission and promotion | Pretraining receipt, canary, and promotion receipt are all `NOT_COMPLETED` | Training remains unauthorized |

## Scope and evidence discipline

This audit evaluates the two proposed SFT-log/GRPO diagnostic frameworks against
the repository's actual contracts. It does not treat literature-derived numeric
thresholds as project authority. A recommendation is accepted only when it is
compatible with the checked-in whole-file C++17 contract and supported by local
tests, stored receipts, or a clearly defined new experiment.

Three evidence classes are kept separate:

| Evidence class | Meaning in this report |
| --- | --- |
| Locally executed | Re-run during this audit on the current worktree |
| Stored execution evidence | Produced previously on the 8xH100 host and verified from logs, receipts, manifests, or tensor dumps |
| Not measured | Cannot be reconstructed from existing artifacts and requires a new instrumented run |

The worktree is dirty and several effective R6 profiles, tests, launchers, reward
files, and documents are untracked. Therefore, revision `19c6824...` alone is not
sufficient to reproduce the audited behavior.

## Bound identities

| Identity | Bound value |
| --- | --- |
| Successful-run profile | `configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-four-topic40.json` |
| Successful-run profile SHA-256 | `dbf0d4c7a92bf549657fb7c7e07bb5a56e1c228d9e8445b0cbaab4919d13a961` |
| Prospective full profile | `configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-full.json` |
| Current full-profile SHA-256 | `e58b623adb7377d98ae26b59c4f3e962fe812e9f966d918fab290bad7c801124` |
| Reward implementation | `src/glm47_posttraining/aider_polyglot/hybrid45.py` |
| Reward implementation SHA-256 | `1edd42f89c409e4c9d03a9a38c604ab9b247c7a8618920f77e84ff7bc9cb057e` |
| Miles reward bridge SHA-256 | `fe06510ac196f2415380f6ccdea4fd207a6d7a87ffe6146eb99df1657c9903ca` |
| Starting adapter | SynthMem-v1 ep50, rank 16, optimizer iteration 649 |
| Starting adapter SHA-256 | `4acb7f23c295f45380155c5d9ee6bc59422262f0cb51f0c02f7e550d405b575a` |
| Model revision | `7dd20894a642a0aa287e9827cb1a1f7f91386b67` |
| Four-topic training manifest SHA-256 | `dbc8fcd1b88859b86d68631e543df735723e0052b0e89617b50aa4ca430340e6` |
| Training image | `sha256:da948662fd1e71801359ec574e6f3299d3129ff9e997be376da394c42d8e942a` |
| Verifier image | `sha256:67d6ae8683ece9022b7599515940404d839f3bff4edaa13a138e894cd58f543a` |
| Iteration-5 training adapter SHA-256 | `7d9194c7579ab5acdcb17c05473e9336e875c20544f67e9a554acd9cb0f4aa68` |
| Iteration-5 serving adapter SHA-256 | `9fa25328b93c4e540df661605ec0af0242e9a9bf6b34241e67dc46a373fe35e8` |

## How the analysis was performed

### Contract review

The authoritative repository files were read before evaluation: `README.md`,
`ROADMAP.md`, `docs/AIDER_SFT_SCOPE.md`, the complete CHARM skill and routed
training/admission references, the Hybrid45 design, the R6 profiles, the Miles
reward bridge, the whole-file parser, the C++ harness, launch scripts, and relevant
tests.

The proposed frameworks were then mapped to the real response, compiler, reward,
optimizer, and admission contracts. Incompatible assumptions were not silently
imported.

### Commands executed

| Command or procedure | Result |
| --- | --- |
| `python3 -m compileall -q src tests` | Passed |
| Focused GRPO/reward/verifier/orchestration pytest set | 240 passed, 3 failed |
| `python3 -m pytest -q` | 577 passed, 4 failed |
| CHARM readiness rule inventory | Completed; all rule families listed |
| CHARM skill quick validation | `Skill is valid!` |
| Local GCC strict C++17 smoke | Passed with GCC 13.3 |
| Local Clang strict C++17 smoke | Passed with Clang 18.1 |
| Exact verifier-image inspection on this host | Not available; image digest was not present locally |
| Local GPU execution | Not available; `nvidia-smi` was absent |
| Six H100 signal-receipt validation | All six receipts parsed and passed their configured gates |
| Safe tensor analysis | `torch.load(..., weights_only=True)` on `grpo_eval_0.pt` and `grpo_eval_5.pt` |
| Deterministic fixed-26 audit generator | Completed for `/tmp/fixed26-clean-run_receipt.json` |

### Local test failures

| Failure | Analysis | Relevance |
| --- | --- | --- |
| Fenced but unlabeled single-file response expected `fatal_parse_failure`, observed `infrastructure_fault` | The parser recovers the sole editable filename with `format_valid=False`, then attempts execution; the local sandbox is unavailable. The test and recovery policy no longer agree. | Reward-contract/test drift; must be resolved before release |
| R6 profile test expects `STANDARD`, profiles specify `SPOT` | Stale test assertion | Configuration reproducibility |
| GRPO data-reuse test expects a literal `DATA_DIR` guard | Runner now correctly supports `MILES_GRPO_PROMPT_DATA`; the test still asserts old text | Stale test assertion |
| CHARM tombstone test expects a missing source assertion | Unrelated to R6 optimization, but the full repository is not green | Repository release hygiene |

The first failure should not be dismissed as only a host problem. The parser's
single-file recovery behavior is real; the unavailable local sandbox merely makes
the contract mismatch surface as `infrastructure_fault`.

## Corrections to the proposed frameworks

| Proposal assumption | Actual R6 contract | Disposition |
| --- | --- | --- |
| SEARCH/REPLACE markers are the canonical format | Exact Aider whole-file filename plus fenced complete replacement | Reject and replace with whole-file checks |
| C++20 and Clang are canonical | Strict GCC 13/C++17 is canonical; Clang is AST/portability evidence | Reject C++20 replacement |
| Four dynamically weighted reward tiers | Nine fixed Hybrid45 tiers and a versioned projection | Reject dynamic reward identity |
| Format failure should remove all later checks | Unreached checks remain in the receipt but are excluded from the observed/applicable optimizer denominator | Keep current causal accounting |
| Style, modularity, and reasoning length should add reward | Style, size, duration, and reasoning length are telemetry only | Keep out of optimizer reward |
| Token entropy must be at least 0.85 | No calibrated definition or baseline is supplied | Do not gate on this number |
| Hidden-state cosine similarity must be at least 0.82 | Hidden states are not captured and the threshold is uncalibrated | Research-only experiment |
| Clipped-token fraction must be 5–15% | The six conservative one-pass updates had 0% clipping and finite gradients | Do not impose this range |
| Dynamic KL target is 0.035 nats | Current run uses static coefficient 0.02; available KL metrics have different meanings | A/B test before changing |
| Peak learning rate should be `2e-6` with warmup/cosine | Current stable profile uses constant `5e-7` | Do not increase before longer canary evidence |
| Dr. GRPO is already active | Realized args show `grpo_std_normalization=True`; trainer source is not vendored | Candidate experiment, not current fact |

## Actual R6 system flow

`Pinned model + SynthMem adapter` ------> `deterministic task projection` ------> `task-local whole-file prompt` ------> `G=8 SGLang rollouts` ------> `thinking/final segmentation` ------> `Hybrid45 static checks` ------> `isolated GCC C++17 verifier` ------> `45-check observation receipt` ------> `Hybrid45 scalar projection` ------> `pre-optimizer signal gate` ------> `GRPO + KL update` ------> `quarantined checkpoint + receipts`

## Hybrid45 reward evaluation

### Implemented reward

Hybrid45 is not the proposed four-term linear reward. It preserves 45 checks but
uses observation-aware bipolar scoring.

| Tier | Weight | Function |
| --- | ---: | --- |
| Forbidden file or bypass | 0.15 | Sandbox, hidden-data, process, escape, and spoofing safety |
| Clarification or no file | 0.05 | Complete substantive payload |
| Fatal parse | 0.05 | Encoding, lexical, fence, preprocessing, and whole-file parsing |
| Wrong label/API | 0.10 | Exact files, public API, namespaces, and editable slots |
| Duplicate file | 0.05 | Canonical path, content, definition, and case-fold collisions |
| Compilation | 0.20 | Syntax, hidden type/API, warnings, link, executable |
| Runtime | 0.10 | Start, no crash, bounded return, clean workspace, handshake |
| Hidden partitions | 0.20 | Five independently executable semantic partitions |
| Full verification | 0.10 | Full grader, sanitizers, bounds, concurrency applicability, repeatability |

For each tier, only kernels that are both observed and applicable enter its
bipolar mean. The scalar projection is:

`R_mix = 0.50 * binary_score + 0.20 * reachability_score + 0.30 * hidden_semantic_score`

Safety is forced to `-1.0`, missing payload is capped at `-0.75`, no-op and
compile/link failures are capped at `0.0`, runtime/sanitizer failures are capped
at `-0.50`, and a complete pass is forced to `+1.0`.

### Why this part is justified

| Property | Evidence |
| --- | --- |
| Exact arithmetic identity | Hybrid45 endpoint and weight tests pass |
| Receipt completeness | Every optimizer record must contain the exact 45 kernels and observation/applicability maps |
| Anti-tamper behavior | Missing kernels, non-bipolar values, and arithmetic changes are rejected |
| Causal credit | Unreached executable checks do not create artificial negative mass in early-format failures |
| Safety floor | Forbidden actions cannot be offset by semantic or style credit |
| Compile/runtime caps | Correctly prevent partial static credit from overwhelming executable failure |
| Infrastructure separation | Verifier faults abort/mask the optimizer batch instead of becoming model reward |
| Functional density | Hidden semantics carry 0.20 tier weight plus 0.30 continuous projection weight |
| Reward anti-hacking | Style, line count, and reasoning length do not add optimizer credit |

### Reward concerns that remain

| Concern | Evidence | Required action |
| --- | --- | --- |
| Documentation says V2 is inactive | Current R6 profiles and stored receipts use `hybrid_bipolar45` | Update the design document status |
| Design requires exact-format rate 0.50 | Current full profile uses 0.35 | Restore one authoritative threshold or document an approved experiment |
| Smoke gate was bypassed | Launch contract records failed 0.39 format gate and `BYPASSED_BY_OPERATOR` | Produce a clean no-bypass smoke receipt |
| Detailed verifier logs disabled | `MILES_CPP_INCLUDE_LOGS=0` hid the low-level concurrency fault | Persist protected failure diagnostics outside model-visible records |
| Production parser recovery drift | One local test now changes a fatal parse into attempted execution | Freeze recovery semantics and update code/tests together |

## Stored H100 execution results

### Memory and failure progression

| Run | Result | Peak memory or failure |
| --- | --- | ---: |
| R3 smoke | Failed before optimizer update | OOM at 80,175 MiB |
| R4 smoke | Failed before optimizer update | OOM at 80,989 MiB |
| R5 smoke | One optimizer update passed | 69,385 MiB |
| R6 failed smoke | Signal gate stopped update | 69,079 MiB; exact format 0.39 |
| R6 full attempt | Stopped before update | Duplicate task groups; 69,081 MiB |
| R6 full retry | Stopped before update | Verifier infrastructure failure; 69,075 MiB |
| R6 four-topic40 | Six optimizer updates passed | 73,339 MiB |

Reducing maximum response length to 16,384 and maximum packed tokens per GPU to
18,432 is therefore justified. Raising response length without a new memory plan
would likely reintroduce the observed OOM failure.

### Six successful signal gates

Each update contained 20 groups and eight samples per group.

| Update | Exact format | Compile among parsed payloads | Positive groups | Semantic-variance groups | Reward-variance groups | Kernel-variance groups | Zero-reward-variance groups |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 70.00% | 99.12% | 17 | 14 | 18 | 19 | 2 |
| 1 | 53.13% | 95.40% | 15 | 10 | 20 | 20 | 0 |
| 2 | 55.63% | 100.00% | 18 | 11 | 20 | 20 | 0 |
| 3 | 65.00% | 97.20% | 16 | 13 | 20 | 20 | 0 |
| 4 | 65.63% | 99.08% | 20 | 13 | 19 | 19 | 1 |
| 5 | 60.63% | 96.00% | 17 | 12 | 20 | 20 | 0 |
| Aggregate | 592/960 = 61.67% | Per-update range 95.40–100% | 103/120 | 73/120 | 117/120 | 118/120 | 3/120 |

This is strong evidence that exact-format SFT weakness remains the main early
bottleneck while compiled responses are usually technically viable. A 100%
format threshold is not realistic for this checkpoint, but 0.35 is too permissive
for an admission gate because the unbypassed smoke contract previously required
0.50 and every successful update subsequently exceeded 0.53.

### Task exposure and sampler behavior

| Update | Groups | Unique task groups | Duplicate group slots |
| ---: | ---: | ---: | ---: |
| 0 | 20 | 18 | 2 |
| 1 | 20 | 16 | 4 |
| 2 | 20 | 16 | 4 |
| 3 | 20 | 18 | 2 |
| 4 | 20 | 17 | 3 |
| 5 | 20 | 16 | 4 |

All 40 tasks received exactly three total exposures, so epoch-level exposure was
correct. Nevertheless, within-update duplicates reduce prompt diversity and make
group-level diagnostics less independent. Disabling the uniqueness check was a
policy relaxation, not a sampler repair.

### Optimizer telemetry

| Update | Gradient norm | Train/rollout KL | Raw KL-loss metric | PPO clip fraction | ESS ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.1555 | 0.1737 | 0.0000 | 0.0 | 1.0 |
| 1 | 0.1531 | 0.1595 | 0.01379 | 0.0 | 1.0 |
| 2 | 0.1582 | 0.1769 | 0.01435 | 0.0 | 1.0 |
| 3 | 0.1167 | 0.1684 | 0.01499 | 0.0 | 1.0 |
| 4 | 0.1518 | 0.1629 | 0.01400 | 0.0 | 1.0 |
| 5 | 0.1614 | 0.1692 | 0.01485 | 0.0 | 1.0 |

Realized optimizer settings were Adam beta1 0.9, beta2 0.98, weight decay 0.1,
constant learning rate `5e-7`, gradient clipping 1.0, epsilon clipping 0.20 with
an upper clip of 0.28, static KL coefficient 0.02, `low_var_kl`, entropy
coefficient zero, and standard GRPO standard-deviation normalization.

The `train/train_rollout_kl` metric is a trainer-versus-rollout-logprob diagnostic,
not automatically the same quantity as the proposal's policy-versus-reference
trajectory KL target. The raw `train/kl_loss` metric is also distinct from the
coefficient-weighted contribution. These values must not be compared to 0.035
without first binding their definitions to the exact Miles source revision.

Near-zero scalar policy-gradient loss is expected at the initial importance
ratio because group-centered advantages sum to approximately zero. Non-zero,
finite gradient norms show that this did not mean a zero-gradient update.

### Rollout length and repetition

| Update | Mean response tokens | Median | Truncated | Repetition flag |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 4,290 | 2,431 | 9.38% | 3.13% |
| 1 | 4,037 | 2,132 | 10.63% | 2.50% |
| 2 | 3,965 | 2,094 | 7.50% | 3.75% |
| 3 | 5,884 | 3,336 | 15.00% | 1.88% |
| 4 | 4,708 | 2,014 | 12.50% | 2.50% |
| 5 | 5,011 | 2,602 | 12.50% | 2.50% |
| Aggregate | — | — | 108/960 = 11.25% | 26/960 = 2.71% |

The proposed completion-before-90%-of-limit condition fails. This is a real
problem because truncated thinking can prevent the complete file payload from
appearing. It should be addressed through format-first generation behavior,
shorter reasoning, and calibrated length controls before increasing the token
limit.

## Development-evaluation diagnostics

The same 60 development prompts were sampled once before update 0 and after
update 5.

| Metric | Eval 0 | Eval 5 | Observation |
| --- | ---: | ---: | --- |
| Mean Hybrid45 reward | -0.24583 | -0.24167 | +0.00417; negligible |
| Reward counts `-1/-0.75/-0.5/0/+1` | 13/7/13/17/10 | 8/6/22/15/9 | Mass shifted from safety floor toward runtime/semantic failure, not toward more full passes |
| Mean response length | 5,464.6 | 5,766.95 | Increased 302.35 tokens |
| Median response length | 3,117.5 | 4,138.5 | Increased substantially |
| Truncated responses | 4/60 | 5/60 | Worsened by one sample |
| Repetition-flagged responses | 1/60 | 4/60 | Worsened, small sample |
| Mean sampled-token NLL | 0.12575 | 0.12495 | Nearly unchanged |
| Maximum unigram token share | 3.78% | 4.03% | No unigram collapse |
| Immediate-token repetition | 0.0107% | 0.0335% | Very low |
| Response-token JS divergence | — | 0.0644 bits | Small-to-moderate descriptive shift; no calibrated gate |
| Response-length KS test | — | statistic 0.1333, p=0.6648 | No detected length-distribution difference at this sample size |
| Paired reward Wilcoxon test | — | statistic 293, p=0.9383 | No detected reward improvement |

The statistical tests are exploratory. There is one stochastic sample per prompt
at each checkpoint and no matched multi-seed training trial. They do not satisfy
the CHARM requirement for at least four matched canary trials.

Full next-token entropy cannot be recovered from sampled-token log probabilities.
The current tensor dumps do not contain the complete vocabulary distribution,
attention matrices, or hidden states.

## Fixed-26 evaluation

The earlier 0/26 run is not used as the model-quality result because its
benchmark compiler inherited the Clang resource include path. The clean rerun is
the valid candidate receipt.

| Metric | SFT base | Clean R6 iteration 5 | Delta |
| --- | ---: | ---: | ---: |
| Pass@1 | 0/26 | 0/26 | 0 |
| Pass@2 | 4/26 | 6/26 | +2 |
| Well formed | 26/26 | 26/26 | 0 |
| Malformed | 0 | 0 | 0 |
| Error outputs | 6 | 11 | +5 |
| Context exhausted | 6 | 11 | +5 |
| Test timeouts | 0 | 0 | 0 |

All six passes were second-try-only: allergies, knapsack, linked-list,
parallel-letter-frequency, space-age, and yacht. The result is therefore mixed:
Pass@2 improved, but Pass@1 did not, context exhaustion worsened, and the run is
only one stochastic evaluation of a quarantined 40-task experiment.

## Detailed disposition of the proposed test matrix

| Proposed test | Current equivalent or evidence | Result | Decision |
| --- | --- | --- | --- |
| TST-PRM-01 delimiter integrity | Exact whole-file filename/fence parser and `format_valid` | 61.67% exact across 960 rollouts | Keep equivalent; improve model/gate |
| TST-PRM-02 context drift | F1–F5, C2/C4, L1/L4/L5, manifest equality | Unit tests pass; unsafe candidates are not executed | Justified |
| TST-COD-01 static compilation | GCC 13, C++17 syntax/API/warning/link checks | 95.4–100% per update among parsed payloads | Justified; do not switch canonical compiler |
| TST-COD-02 memory cleanliness | ASan/UBSan/LSan plus applicable TSan | Non-concurrent subset passed; full concurrency task caused infrastructure abort | Partial; repair full path |
| TST-TKN-01 entropy/repetition | Repetition flag exists; exact entropy disabled and not stored | Repetition 1.88–3.75%; entropy unavailable | Add telemetry, no arbitrary threshold |
| TST-TKN-02 length saturation | Response length and truncation metrics | 7.5–15% truncation | Failed; high priority |
| TST-LAT-01 sink-token drift | No attention matrices retained | Not measured | Optional research only |
| TST-LAT-02 hidden drift | No hidden-state baseline or captures | Not measured | Optional research only |
| TST-WB-01 advantage explosion | Reward-variance gate, gradient norm, zero-std logging | 3/120 homogeneous groups; finite gradients | Stable short run; add exact advantage telemetry |
| TST-WB-02 ratio saturation | `pg_clipfrac`, `ppo_kl`, ESS | 0%, 0, and 1.0 on all six steps | Conservative updates; proposed 5–15% range rejected |
| Context-pollution tests | Two-message task-local prompt, rubric-free prompt tests, static escape checks | Unit tests pass | Justified |
| Reward-ranking controls | Reference, compile-failure, no-op, and safety-bypass no-update controls | Stored control receipt passed | Justified |
| Multi-run significance | CHARM requires matched trials | Not performed | Required before promotion |

## Parts of the current setup that are justified

| Component | Why it should remain |
| --- | --- |
| Aider whole-file output | Matches the benchmark and current parser; SEARCH/REPLACE would train the wrong protocol |
| Strict C++17 | Repository and task contract; changing to C++20 would change the target behavior |
| GCC primary, Clang secondary | GCC matches executable verification; Clang adds AST and portability evidence without redefining correctness |
| Hybrid45 fixed identity | Prevents reward semantics from changing mid-run and preserves exact receipts |
| Observation-aware denominators | Avoids treating unreachable checks as independent model failures |
| Safety and failure caps | Prevent reward compensation across causal boundaries |
| Five hidden partitions | Supplies independent semantic density rather than a single all-or-nothing test |
| Fail-closed infrastructure handling | Stops infrastructure faults from poisoning optimizer labels |
| Group size eight | Produced useful reward/kernel variance with manageable memory |
| Temperature 0.7 | Produced diverse rewards without observed token collapse |
| Learning rate `5e-7` | Six finite conservative updates; no evidence supports increasing it yet |
| Gradient clip 1.0 | Correct guardrail; observed norms remained far below it |
| Static KL coefficient 0.02 | Stable over six updates; should remain until a matched KL experiment exists |
| 16,384 response and 18,432 packed-token limits | Prevented the observed 80 GiB OOMs |
| Style/length as telemetry | Prevents easy reward hacking and semantic compensation |
| Quarantine/admission labels | Truthfully prevent an engineering run from becoming a promoted checkpoint |

## Required updates

### P0: must be resolved before another full 475-task attempt

| Update | Required proof |
| --- | --- |
| Repair concurrency/TSan verifier infrastructure | Preserve protected low-level logs; reproduce `concurrent-tag-factory`; classify candidate failure versus infrastructure failure; pass isolated preflight and task replay |
| Fix within-batch task sampling | Every 25-group full batch must contain 25 unique task IDs while preserving the exact three-epoch exposure ledger |
| Eliminate operator smoke bypass | Run the same profile through no-update canary and one-update smoke with no authorization bypass and exact receipts |
| Reduce rollout truncation | Demonstrate a materially lower truncation rate without returning to OOM; admission target should be zero prompt truncation and an explicitly bounded response-truncation policy |
| Resolve parser recovery semantics | Decide whether an unlabeled single-file fence is recoverable; make parser, reward reason, execution policy, and tests agree |
| Restore a green focused suite | Fix the SPOT assertion and prompt-data guard assertion; do not launch from a tree with reward/orchestration failures |
| Commit the effective R6 surface | Profiles, launchers, reward code, tests, and smoke certification must be reproducible from a named revision |

### P1: required before admission or promotion

| Update | Required proof |
| --- | --- |
| Reconcile format threshold | One authoritative value in design, profile, launcher, and tests; 0.50 is supported by the successful batches, while 0.35 is an unexplained relaxation |
| Reconcile development counts | Profile contains both 60 and 64 development targets; bind source targets, selected evaluation rows, and prompt variants separately |
| Update stale Hybrid45 status documentation | Document that R6 actually selects Hybrid45 V2 while remaining unadmitted |
| Vendor or digest-bind Miles advantage code | Prove standardization epsilon, homogeneous-group behavior, and exact zero-gradient semantics with deterministic tests |
| Add advantage telemetry | Per-group reward mean/std, advantage max/variance, homogeneous-group count, and non-finite checks |
| Add explicit reference-KL telemetry | Log a clearly named, definition-bound policy/reference KL separately from trainer/rollout mismatch KL |
| Preserve protected verifier failures | Keep detailed compiler/sanitizer/runtime evidence in access-controlled receipts without exposing private tests to model rows |
| Run canonical matched canary | Exactly 20 tasks x5 epochs, at least four matched trials, followed by the frozen promotion selector |
| Validate full-corpus no-update replay | All 475 selected tasks must produce valid infrastructure-separated reward receipts before optimizer authorization |
| Repeat clean fixed-26 evaluation | Matched seeds/settings and receipt-backed comparison; require strict Pass@1 improvement for promotion |

### P2: useful diagnostics after the blockers above

| Candidate | Conditions |
| --- | --- |
| Full token entropy | Capture calibrated entropy summaries without retaining unnecessary logits; establish baseline bands first |
| JS drift monitor | Use fixed prompts and tokenizer identity; treat as telemetry until correlated with correctness |
| Dr. GRPO/mean-only advantage | A/B against current standardization on identical batches, including all-equal rewards and low-variance groups |
| Dynamic KL controller | Separate optimizer experiment with rollback tests and a precisely defined KL signal |
| Hidden-state or attention drift | Research-only run with predefined layers, pooling, baselines, storage budget, and correlation analysis |
| Reasoning-efficiency intervention | Prefer prompt/SFT/curriculum changes; do not add a raw token-count reward until reward-hacking controls exist |

## Recommendations rejected for the current optimizer

| Recommendation | Reason for rejection |
| --- | --- |
| Switch canonical verification to Clang/C++20 | Violates the C++17 target and changes portability evidence into the source of truth |
| Require SEARCH/REPLACE tags | Trains the wrong Aider response protocol |
| Dynamically change reward weights by training step | Changes reward identity and makes cross-step comparisons ambiguous |
| Add Clang-format or modularity reward | Can compensate for semantic failure and is not reference-normalized |
| Penalize every reasoning token | Encourages premature answers and can suppress necessary reasoning |
| Force entropy >=0.85 | Undefined scale and no matched baseline |
| Force hidden-state cosine >=0.82 | No layer/pooling/reference calibration and no stored states |
| Force 5–15% PPO clipping | Would reject the observed stable conservative updates without evidence of benefit |
| Increase LR to `2e-6` now | Fourfold increase is unsupported by only six updates and conflicts with current stability evidence |
| Start full 57-update training now | Full-corpus verifier, sampler, smoke, admission, and canary gates are incomplete |

## Formal status

| Status surface | Result |
| --- | --- |
| Local Python compilation | Passed |
| Full repository pytest | Failed: 577 passed, 4 failed |
| Reward arithmetic/unit contract | Passed in focused tests |
| Real no-update Hybrid45 controls | Passed in stored H100 receipt |
| One-update memory smoke | Passed in R5 |
| Six-update selected-subset execution | Passed |
| Full 475-task execution | Failed before optimizer update |
| Clean fixed-26 benchmark | Mixed: Pass@2 +2, Pass@1 unchanged, context exhaustion +5 |
| Pretraining admission | `NOT_COMPLETED` |
| Canonical CHARM canary | `NOT_COMPLETED` |
| Promotion | `NOT_COMPLETED` |
| Checkpoint disposition | `QUARANTINE_ONLY` |

No evidence in this audit authorizes full training, retroactive admission,
checkpoint promotion, or deployment.
