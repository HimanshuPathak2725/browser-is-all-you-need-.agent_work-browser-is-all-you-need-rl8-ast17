# GLM-4.7 Aider AST17 SFT And GRPO Results

This document combines the exact AST17 SFT checkpoint selected for GRPO with the successful GRPO run that continued from it. The SFT section reports training-health metrics for the selected checkpoint. The GRPO section reports training metrics plus the monitor-eval rewards assigned during GRPO.

Important limitation: the local evidence does not contain an exact fixed-26 Aider evaluation receipt for the `ast17-sft1425` SFT checkpoint or for the final `035206` GRPO checkpoint. Therefore this file should not be used as proof of pass@1/pass@2 improvement over SFT. It is a training and monitor-eval evidence report.

## Source Files

| File | Contains |
| --- | --- |
| `docs/glm47-aider-ast17-sft1425-performance.md` | Detailed SFT checkpoint, dataset, training, and integrity report. |
| `docs/glm47-aider-ast17-grpo-035206-training-performance.md` | Successful GRPO run identity and per-update training chart. |
| `docs/glm47-aider-ast17-grpo-035206-eval-rewards.md` | Detailed GRPO monitor-eval reward tables. |
| `docs/glm47-aider-ast17-grpo-035206-eval-rewards.json` | Parsed machine-readable reward rows from all 26 monitor eval dumps. |

## Checkpoint Lineage

| Stage | Run ID | Checkpoint / Iteration | Adapter path | Adapter SHA-256 | Status |
| --- | --- | --- | --- | --- | --- |
| SFT | `glm47-aider-ast17-sft1425-20260723-141256` | `iter_0000070` | `/workspace/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` | `success` |
| GRPO | `glm47-aider-ast17-grpo-main-20260724-035206` | `iter_0000025` | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/checkpoints/grpo_lora_r16/iter_0000025/adapter` | `aa75e8eaae36465b959de06286196e3cc9dd19c8d46d3cda8277fcaa05323c95` | `success`, training gate `passed` |

## Dataset And Eval Coverage

| Item | SFT | GRPO |
| --- | ---: | ---: |
| Training data | `1425` packaged rows, `1420` consumed/logged | `253` GRPO train tasks |
| Train data manifest SHA-256 | `813637ced3078c661a857f7e858d43ab0390684366f41f68bbd6a703899f39a6` | `b1533088916a0d795c55ec7ff7a1fa11de924ed7c0b38c88ff9f736b48f1ce9c` |
| Training split path | `.glm47-posttraining/imported_aider_data_sft1425/sft/train.jsonl` | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/data/grpo/train.jsonl` |
| Monitor eval split | Not logged for exact SFT run | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/data/eval/train_monitor.jsonl` |
| Monitor eval tasks | Not available | `32` tasks x `26` evals = `832` reward assignments |
| Exact fixed-26 eval receipt | Not found locally | Not found locally |

## SFT Training Result

| Metric | Value |
| --- | ---: |
| Run status | `success` |
| Wall time | `1229 s` (~20m 29s) |
| Update steps | `71`, steps `0..70` |
| Selected checkpoint | `iter_0000070` |
| Peak GPU memory | `72363 MiB` |
| First train loss | `0.403495` |
| Final train loss | `0.156413` |
| Loss reduction | `61.2%` |
| Mean train loss | `0.286823` |
| Median train loss | `0.279888` |
| First grad norm | `0.703228` |
| Final grad norm | `0.194224` |
| Mean grad norm | `0.416194` |
| Truncation ratio | `0.0` |
| Mean rollout response length | `824.45` tokens |
| Exact SFT eval result | Not measured in local evidence |

Interpretation: the SFT checkpoint trained cleanly, with a large supervised-loss reduction and stable gradients. This is optimization evidence, not held-out task-quality evidence.

## GRPO Training Result

| Metric | First | Best / Min | Final | Mean |
| --- | ---: | ---: | ---: | ---: |
| Train loss | `-0.000000` @ step 0 | min `-0.000000` @ step 0 | `0.000204` @ step 25 | `0.000172` |
| KL loss | `-0.000000` @ step 0 | max `0.010192` @ step 25 | `0.010192` @ step 25 | `0.008597` |
| Raw rollout reward | `-0.564453` @ rollout 0 | best `-0.533203` @ rollout 20 | `-0.553125` @ rollout 25 | `-0.549594` |
| Monitor eval reward | `-0.546875` @ eval 0 | best `-0.509375` @ eval 15 and 22 | `-0.537500` @ eval 25 | `-0.540625` |
| Passrate logger | `0.0` | `0.0` | `0.0` | `0.0` |

| GRPO Setting | Value |
| --- | --- |
| Algorithm | `GRPO` advantage estimator with KL regularization |
| Rollout updates | `26 / 26` |
| Rollout batch size | `32` prompts |
| Samples per prompt | `8` |
| Global batch size | `256` |
| KL loss coefficient | `0.02` |
| Learning rate | `5e-7`, constant |
| LoRA rank / alpha | `16 / 32` |
| Sequence length | `6144` |
| Max response length | `4096` |
| Wall time | `9511 s` (~2h 38m) |
| Peak GPU memory | `69189 MiB` |

## SFT To GRPO Comparison

| Question | Answer from available evidence |
| --- | --- |
| Did GRPO complete from the selected SFT checkpoint? | Yes. The final GRPO checkpoint is gated and has a distinct final adapter hash. |
| Did GRPO show reward movement? | Slightly. Monitor eval moved from `-0.546875` to `-0.537500`; best monitor eval was `-0.509375`. |
| Did GRPO show pass@1/pass@2 improvement? | Not proven. Training-loop passrate stayed `0.0`, and no exact fixed-26 eval receipt is present. |
| Is the monitor eval comparable to fixed-26 Aider eval? | No. It uses `train_monitor.jsonl` with 32 monitor tasks during GRPO. |
| Main failure mode in GRPO monitor eval | Compilation failure dominated: `722 / 832` reward assignments. |

## GRPO Monitor Eval Reward Policy

| Reward reason | Assigned reward | Count across 832 assignments | Total negative contribution | Mean contribution |
| --- | ---: | ---: | ---: | ---: |
| `compilation_failure` | `-0.50` | `722` | `-361.0` | `-0.5000` |
| `fatal_parse_failure` | `-0.80` | `106` | `-84.8` | `-0.8000` |
| `forbidden_file_or_primitive_violation` | `-1.00` | `4` | `-4.0` | `-1.0000` |

## GRPO Per-Eval Reward Chart

| Eval | Mean reward | Total reward | Best | Worst | Passes | Format valid | Compile errors | Reason counts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| E00 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `26/32` | `27/32` | compilation_failure=27; fatal_parse_failure=5 |
| E01 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `26/32` | `27/32` | compilation_failure=27; fatal_parse_failure=5 |
| E02 | `-0.540625` | `-17.3` | `-0.50` | `-1.00` | `0/32` | `29/32` | `29/32` | compilation_failure=29; forbidden_file_or_primitive_violation=2; fatal_parse_failure=1 |
| E03 | `-0.556250` | `-17.8` | `-0.50` | `-0.80` | `0/32` | `25/32` | `26/32` | compilation_failure=26; fatal_parse_failure=6 |
| E04 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `28/32` | `29/32` | compilation_failure=29; fatal_parse_failure=3 |
| E05 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E06 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E07 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `25/32` | `27/32` | compilation_failure=27; fatal_parse_failure=5 |
| E08 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E09 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `25/32` | `25/32` | compilation_failure=25; fatal_parse_failure=7 |
| E10 | `-0.518750` | `-16.6` | `-0.50` | `-0.80` | `0/32` | `30/32` | `30/32` | compilation_failure=30; fatal_parse_failure=2 |
| E11 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `28/32` | `29/32` | compilation_failure=29; fatal_parse_failure=3 |
| E12 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E13 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `25/32` | `25/32` | compilation_failure=25; fatal_parse_failure=7 |
| E14 | `-0.584375` | `-18.7` | `-0.50` | `-0.80` | `0/32` | `23/32` | `23/32` | compilation_failure=23; fatal_parse_failure=9 |
| E15 | `-0.509375` | `-16.3` | `-0.50` | `-0.80` | `0/32` | `30/32` | `31/32` | compilation_failure=31; fatal_parse_failure=1 |
| E16 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `29/32` | `29/32` | compilation_failure=29; fatal_parse_failure=3 |
| E17 | `-0.562500` | `-18.0` | `-0.50` | `-1.00` | `0/32` | `26/32` | `26/32` | compilation_failure=26; fatal_parse_failure=5; forbidden_file_or_primitive_violation=1 |
| E18 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `28/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E19 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `29/32` | `29/32` | compilation_failure=29; fatal_parse_failure=3 |
| E20 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `24/32` | `25/32` | compilation_failure=25; fatal_parse_failure=7 |
| E21 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E22 | `-0.509375` | `-16.3` | `-0.50` | `-0.80` | `0/32` | `29/32` | `31/32` | compilation_failure=31; fatal_parse_failure=1 |
| E23 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |
| E24 | `-0.525000` | `-16.8` | `-0.50` | `-1.00` | `0/32` | `29/32` | `30/32` | compilation_failure=30; fatal_parse_failure=1; forbidden_file_or_primitive_violation=1 |
| E25 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | compilation_failure=28; fatal_parse_failure=4 |

## GRPO Per-Task Aggregate Reward Table

This table aggregates all 26 monitor-eval reward assignments for each task. Higher reward is better because all observed reward values are negative.

| Task | Mean reward | Total reward | Best | Worst | Final E25 | Final reason | Passes | Format valid | Compile errors | Fatal parse | Forbidden | Reason counts |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `aider-shadow-cpp/cpu-block-prefix-suffix-peaks` | `-0.592308` | `-15.4` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `17/26` | `18/26` | `8/26` | `0/26` | compilation_failure=18; fatal_parse_failure=8 |
| `aider-shadow-cpp/curfew-dispatch-selector` | `-0.580769` | `-15.1` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `19/26` | `19/26` | `7/26` | `0/26` | compilation_failure=19; fatal_parse_failure=7 |
| `aider-shadow-cpp/reflow-nested-quotes` | `-0.580769` | `-15.1` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `18/26` | `19/26` | `7/26` | `0/26` | compilation_failure=19; fatal_parse_failure=7 |
| `aider-shadow-cpp/warranty-service-calendar` | `-0.573077` | `-14.9` | `-0.50` | `-1.00` | `-0.80` | `fatal_parse_failure` | `0/26` | `21/26` | `21/26` | `3/26` | `2/26` | compilation_failure=21; fatal_parse_failure=3; forbidden_file_or_primitive_violation=2 |
| `aider-shadow-cpp/dated-project-burnup` | `-0.569231` | `-14.8` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `20/26` | `20/26` | `6/26` | `0/26` | compilation_failure=20; fatal_parse_failure=6 |
| `aider-shadow-cpp/protected-whitespace-runs` | `-0.565385` | `-14.7` | `-0.50` | `-1.00` | `-0.50` | `compilation_failure` | `0/26` | `18/26` | `21/26` | `4/26` | `1/26` | compilation_failure=21; fatal_parse_failure=4; forbidden_file_or_primitive_violation=1 |
| `aider-shadow-cpp/copy-loan-ledger` | `-0.557692` | `-14.5` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `18/26` | `21/26` | `5/26` | `0/26` | compilation_failure=21; fatal_parse_failure=5 |
| `aider-shadow-cpp/offset-deployment-quorum-sweep` | `-0.557692` | `-14.5` | `-0.50` | `-0.80` | `-0.80` | `fatal_parse_failure` | `0/26` | `20/26` | `21/26` | `5/26` | `0/26` | compilation_failure=21; fatal_parse_failure=5 |
| `aider-shadow-cpp/ski-elevation-dag` | `-0.557692` | `-14.5` | `-0.50` | `-0.80` | `-0.80` | `fatal_parse_failure` | `0/26` | `21/26` | `21/26` | `5/26` | `0/26` | compilation_failure=21; fatal_parse_failure=5 |
| `aider-shadow-cpp/deque-lexicographic-end-picker` | `-0.546154` | `-14.2` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `20/26` | `22/26` | `4/26` | `0/26` | compilation_failure=22; fatal_parse_failure=4 |
| `aider-shadow-cpp/epoch-span-partitioner` | `-0.546154` | `-14.2` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `22/26` | `22/26` | `4/26` | `0/26` | compilation_failure=22; fatal_parse_failure=4 |
| `aider-shadow-cpp/snowplow-edge-router` | `-0.546154` | `-14.2` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `21/26` | `22/26` | `4/26` | `0/26` | compilation_failure=22; fatal_parse_failure=4 |
| `aider-shadow-cpp/status-panel-decimator` | `-0.546154` | `-14.2` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `22/26` | `22/26` | `4/26` | `0/26` | compilation_failure=22; fatal_parse_failure=4 |
| `aider-shadow-cpp/shelf-empty-span-index` | `-0.542308` | `-14.1` | `-0.50` | `-1.00` | `-0.50` | `compilation_failure` | `0/26` | `23/26` | `23/26` | `2/26` | `1/26` | compilation_failure=23; fatal_parse_failure=2; forbidden_file_or_primitive_violation=1 |
| `aider-shadow-cpp/broadcast-break-stab-v2` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `22/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/bst-price-level-book-v2` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `23/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/crc-byte-register` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `21/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/hotspot-row-sweep` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.80` | `fatal_parse_failure` | `0/26` | `23/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/keyboard-transition-coalescer` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `22/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/leap-coverage-segments` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `23/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/radix-command-catalog` | `-0.534615` | `-13.9` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `23/26` | `23/26` | `3/26` | `0/26` | compilation_failure=23; fatal_parse_failure=3 |
| `aider-shadow-cpp/factory-z-cycle-v2` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/oil-tide-wrap` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `21/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/podcast-attempt-selector` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/quay-concession-component-audit` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/ridge-height-silhouette` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/skip-gap-calendar` | `-0.523077` | `-13.6` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `24/26` | `2/26` | `0/26` | compilation_failure=24; fatal_parse_failure=2 |
| `aider-shadow-cpp/calibration-run-index` | `-0.511538` | `-13.3` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `22/26` | `25/26` | `1/26` | `0/26` | compilation_failure=25; fatal_parse_failure=1 |
| `aider-shadow-cpp/defect-pareto-matrix` | `-0.511538` | `-13.3` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `24/26` | `25/26` | `1/26` | `0/26` | compilation_failure=25; fatal_parse_failure=1 |
| `aider-shadow-cpp/ranked-lap-recap` | `-0.511538` | `-13.3` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `25/26` | `25/26` | `1/26` | `0/26` | compilation_failure=25; fatal_parse_failure=1 |
| `aider-shadow-cpp/time-parking-grace-audit` | `-0.511538` | `-13.3` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `25/26` | `25/26` | `1/26` | `0/26` | compilation_failure=25; fatal_parse_failure=1 |
| `aider-shadow-cpp/timer-oven-safety-lock` | `-0.511538` | `-13.3` | `-0.50` | `-0.80` | `-0.50` | `compilation_failure` | `0/26` | `25/26` | `25/26` | `1/26` | `0/26` | compilation_failure=25; fatal_parse_failure=1 |

## Final Verdict

The exact SFT checkpoint is a valid training-success checkpoint and the GRPO run completed successfully from it. The GRPO monitor reward shows a small, noisy lift, but the available evidence does not establish held-out pass@1/pass@2 improvement over SFT. The next required artifact for that claim is a fixed-26 eval receipt for the final GRPO adapter and, ideally, the exact SFT adapter.

## Reward Rubric Update After This Run

The monitor eval showed that the previous production reward was too sparse for GRPO: `832` assignments collapsed into only three reward values, with `722 / 832` samples landing on the same `compilation_failure = -0.50` bucket. The updated Aider production reward policy is implemented in `src/glm47_posttraining/aider_polyglot/reward.py` and documented in `docs/glm47-aider-ast17-grpo-reward-policy-v2.md`.

| Previous Problem | Updated Policy |
| --- | --- |
| Compile failures were flat. | Compile failures are now split by diagnostic class: syntax, missing symbol, missing include/type, API mismatch, linker issue, and warning-as-error. |
| Fatal parse failures were flat. | Parse failures now distinguish forbidden edits, clarification/no-file output, fatal parse, duplicate files, and wrong file labels. |
| No positive signal appeared before full pass. | Compile-and-run with zero tests now receives a small positive reward band, and partial tests use `0.15 + 0.60*S_tests + bounded bonuses`. |
| AST/style activated too late. | Pre-pass shaping now includes exact Aider format, basic mechanism signal, and independent C++ quality after safe parsing. |
| Style duplicated AST17 telemetry. | `s_style` now uses independent C++ quality checks instead of copying `s_ast17`. |
| Full pass had no hard floor. | Any all-tests-pass candidate is floored at `0.85`, with clean full passes shaped toward `0.90..1.00`. |
| Recoverable Aider format was not visible enough. | Recoverable-format cases keep a `recoverable_format_...` reason prefix for W&B/artifact analysis. |

| Outcome | Updated Reward | Reason / Bucket |
| --- | ---: | --- |
| Forbidden file, test edit, CMake edit, path escape, verifier bypass | `-1.00` | `forbidden_file_or_primitive_violation` |
| Clarification-only answer or no file output | `-0.92` | `clarification_or_no_file_output` |
| Fatal parse failure with no recoverable editable file | `-0.85` | `fatal_parse_failure` |
| Wrong non-protected file label with code present | `-0.75` | `wrong_file_label` |
| Duplicate editable file block | `-0.70` | `duplicate_file` |
| Recoverable Aider format with editable code extracted | shaped by downstream verifier | `recoverable_format_*` prefix |
| Severe compile syntax failure | `-0.55` | `compilation_failure_syntax` |
| Missing symbol / missing include or type / API mismatch / linker / warning-as-error | `-0.50` to `-0.30` | diagnostic-specific compile buckets |
| Compiles and runs, zero tests pass | `0.05` to `0.12` | `runtime_zero_pass` |
| Partial tests pass | `0.15 + 0.60*S_tests + small bonuses`, cap `0.80` | `partial_test_pass` |
| Full hidden-test pass | `max(0.85, shaped_score)` | `correct` |
| Clean full pass with AST/style/safety shaping | `0.90` to `1.00` | `correct` with higher shaped score |

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
