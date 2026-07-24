# GLM-4.7 Aider AST17 GRPO Eval Reward Table

This document records the reward assigned to each task during the successful GRPO run monitor evaluation. The values come from the saved `grpo_eval_*.pt` reward dumps, not from a separate fixed-26 benchmark receipt.

## Run Identity

| Field | Value |
| --- | --- |
| GRPO run ID | `glm47-aider-ast17-grpo-main-20260724-035206` |
| Run status | `success` |
| GRPO updates completed | `26 / 26` |
| Monitor eval dumps parsed | `26` |
| Unique monitor-eval tasks | `32` |
| Reward assignments parsed | `832` |
| Monitor eval split | `data/eval/train_monitor.jsonl` |
| Eval dump source | `/tmp/grpo_035206_eval_dumps` |
| Final checkpoint | `iter_0000025` |
| Final adapter path | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Final adapter SHA-256 | `aa75e8eaae36465b959de06286196e3cc9dd19c8d46d3cda8277fcaa05323c95` |
| Source SFT adapter | `/workspace/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Source SFT adapter SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| Training data manifest SHA-256 | `b1533088916a0d795c55ec7ff7a1fa11de924ed7c0b38c88ff9f736b48f1ce9c` |

## Reward Policy Observed

| Reward reason | Assigned reward | Count across 832 assignments | Total contribution | Mean contribution |
| --- | ---: | ---: | ---: | ---: |
| `compilation_failure` | `-0.50` | `722` | `-361.0` | `-0.5000` |
| `fatal_parse_failure` | `-0.80` | `106` | `-84.8` | `-0.8000` |
| `forbidden_file_or_primitive_violation` | `-1.00` | `4` | `-4.0` | `-1.0000` |

## Evaluation Summary

| Metric | Value |
| --- | ---: |
| First eval mean reward, E00 | `-0.546875` |
| Final eval mean reward, E25 | `-0.537500` |
| Best eval mean reward | `E15 = -0.509375` |
| Worst eval mean reward | `E14 = -0.584375` |
| Final eval pass count | `0 / 32` |
| All-eval pass assignments | `0 / 832` |
| All-eval format-valid assignments | `699 / 832` |

## Per-Eval Reward Chart

| Eval | Mean reward | Total reward | Best | Worst | Passes | Format valid | Compile errors | Timeouts | Reason counts |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| E00 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `26/32` | `27/32` | `0` | compilation_failure=27; fatal_parse_failure=5 |
| E01 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `26/32` | `27/32` | `0` | compilation_failure=27; fatal_parse_failure=5 |
| E02 | `-0.540625` | `-17.3` | `-0.50` | `-1.00` | `0/32` | `29/32` | `29/32` | `0` | compilation_failure=29; forbidden_file_or_primitive_violation=2; fatal_parse_failure=1 |
| E03 | `-0.556250` | `-17.8` | `-0.50` | `-0.80` | `0/32` | `25/32` | `26/32` | `0` | compilation_failure=26; fatal_parse_failure=6 |
| E04 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `28/32` | `29/32` | `0` | compilation_failure=29; fatal_parse_failure=3 |
| E05 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E06 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E07 | `-0.546875` | `-17.5` | `-0.50` | `-0.80` | `0/32` | `25/32` | `27/32` | `0` | compilation_failure=27; fatal_parse_failure=5 |
| E08 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E09 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `25/32` | `25/32` | `0` | compilation_failure=25; fatal_parse_failure=7 |
| E10 | `-0.518750` | `-16.6` | `-0.50` | `-0.80` | `0/32` | `30/32` | `30/32` | `0` | compilation_failure=30; fatal_parse_failure=2 |
| E11 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `28/32` | `29/32` | `0` | compilation_failure=29; fatal_parse_failure=3 |
| E12 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E13 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `25/32` | `25/32` | `0` | compilation_failure=25; fatal_parse_failure=7 |
| E14 | `-0.584375` | `-18.7` | `-0.50` | `-0.80` | `0/32` | `23/32` | `23/32` | `0` | compilation_failure=23; fatal_parse_failure=9 |
| E15 | `-0.509375` | `-16.3` | `-0.50` | `-0.80` | `0/32` | `30/32` | `31/32` | `0` | compilation_failure=31; fatal_parse_failure=1 |
| E16 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `29/32` | `29/32` | `0` | compilation_failure=29; fatal_parse_failure=3 |
| E17 | `-0.562500` | `-18.0` | `-0.50` | `-1.00` | `0/32` | `26/32` | `26/32` | `0` | compilation_failure=26; fatal_parse_failure=5; forbidden_file_or_primitive_violation=1 |
| E18 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `28/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E19 | `-0.528125` | `-16.9` | `-0.50` | `-0.80` | `0/32` | `29/32` | `29/32` | `0` | compilation_failure=29; fatal_parse_failure=3 |
| E20 | `-0.565625` | `-18.1` | `-0.50` | `-0.80` | `0/32` | `24/32` | `25/32` | `0` | compilation_failure=25; fatal_parse_failure=7 |
| E21 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `27/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E22 | `-0.509375` | `-16.3` | `-0.50` | `-0.80` | `0/32` | `29/32` | `31/32` | `0` | compilation_failure=31; fatal_parse_failure=1 |
| E23 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |
| E24 | `-0.525000` | `-16.8` | `-0.50` | `-1.00` | `0/32` | `29/32` | `30/32` | `0` | compilation_failure=30; fatal_parse_failure=1; forbidden_file_or_primitive_violation=1 |
| E25 | `-0.537500` | `-17.2` | `-0.50` | `-0.80` | `0/32` | `26/32` | `28/32` | `0` | compilation_failure=28; fatal_parse_failure=4 |

## Per-Task Aggregate Rewards

Each row aggregates the 26 monitor-eval reward assignments for one task. Higher reward is better because all observed rewards are negative.

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

## Per-Task Reward Matrix

This matrix shows the exact reward assigned to each task at each monitor evaluation. `E00` is the first eval and `E25` is the final eval after update 25.

| Task | E00 | E01 | E02 | E03 | E04 | E05 | E06 | E07 | E08 | E09 | E10 | E11 | E12 | E13 | E14 | E15 | E16 | E17 | E18 | E19 | E20 | E21 | E22 | E23 | E24 | E25 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `aider-shadow-cpp/broadcast-break-stab-v2` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/bst-price-level-book-v2` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/calibration-run-index` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/copy-loan-ledger` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/cpu-block-prefix-suffix-peaks` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/crc-byte-register` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/curfew-dispatch-selector` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` |
| `aider-shadow-cpp/dated-project-burnup` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/defect-pareto-matrix` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/deque-lexicographic-end-picker` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/epoch-span-partitioner` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/factory-z-cycle-v2` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/hotspot-row-sweep` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` |
| `aider-shadow-cpp/keyboard-transition-coalescer` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/leap-coverage-segments` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/offset-deployment-quorum-sweep` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` |
| `aider-shadow-cpp/oil-tide-wrap` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/podcast-attempt-selector` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/protected-whitespace-runs` | `-0.50` | `-0.80` | `-1.00` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/quay-concession-component-audit` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/radix-command-catalog` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/ranked-lap-recap` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/reflow-nested-quotes` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/ridge-height-silhouette` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/shelf-empty-span-index` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-1.00` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/ski-elevation-dag` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.80` |
| `aider-shadow-cpp/skip-gap-calendar` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/snowplow-edge-router` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/status-panel-decimator` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/time-parking-grace-audit` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/timer-oven-safety-lock` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` |
| `aider-shadow-cpp/warranty-service-calendar` | `-0.50` | `-0.50` | `-1.00` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.80` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-0.50` | `-1.00` | `-0.80` |

## Final Eval Task Rewards

These are the rewards assigned in the last monitor evaluation, `E25`, using the final checkpoint.

| Task | Reward | Reason | Format valid | Compile error | Tests passed | All tests pass | Return code | Response length | Modified files |
| --- | ---: | --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| `aider-shadow-cpp/broadcast-break-stab-v2` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `536` | `2` |
| `aider-shadow-cpp/bst-price-level-book-v2` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1766` | `2` |
| `aider-shadow-cpp/calibration-run-index` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `666` | `2` |
| `aider-shadow-cpp/copy-loan-ledger` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `812` | `2` |
| `aider-shadow-cpp/cpu-block-prefix-suffix-peaks` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `644` | `2` |
| `aider-shadow-cpp/crc-byte-register` | `-0.50` | `compilation_failure` | `no` | `yes` | `0/0` | `no` | `254` | `497` | `2` |
| `aider-shadow-cpp/curfew-dispatch-selector` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `714` | `1` |
| `aider-shadow-cpp/dated-project-burnup` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1710` | `2` |
| `aider-shadow-cpp/defect-pareto-matrix` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1235` | `1` |
| `aider-shadow-cpp/deque-lexicographic-end-picker` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `415` | `2` |
| `aider-shadow-cpp/epoch-span-partitioner` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1353` | `1` |
| `aider-shadow-cpp/factory-z-cycle-v2` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `699` | `2` |
| `aider-shadow-cpp/hotspot-row-sweep` | `-0.80` | `fatal_parse_failure` | `no` | `no` | `0/0` | `no` | `` | `199` | `0` |
| `aider-shadow-cpp/keyboard-transition-coalescer` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `752` | `2` |
| `aider-shadow-cpp/leap-coverage-segments` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `609` | `1` |
| `aider-shadow-cpp/offset-deployment-quorum-sweep` | `-0.80` | `fatal_parse_failure` | `no` | `no` | `0/0` | `no` | `` | `4096` | `0` |
| `aider-shadow-cpp/oil-tide-wrap` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1192` | `1` |
| `aider-shadow-cpp/podcast-attempt-selector` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `497` | `2` |
| `aider-shadow-cpp/protected-whitespace-runs` | `-0.50` | `compilation_failure` | `no` | `yes` | `0/0` | `no` | `254` | `1476` | `1` |
| `aider-shadow-cpp/quay-concession-component-audit` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1162` | `2` |
| `aider-shadow-cpp/radix-command-catalog` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1615` | `2` |
| `aider-shadow-cpp/ranked-lap-recap` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `688` | `2` |
| `aider-shadow-cpp/reflow-nested-quotes` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `453` | `2` |
| `aider-shadow-cpp/ridge-height-silhouette` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `335` | `1` |
| `aider-shadow-cpp/shelf-empty-span-index` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `740` | `2` |
| `aider-shadow-cpp/ski-elevation-dag` | `-0.80` | `fatal_parse_failure` | `no` | `no` | `0/0` | `no` | `` | `2376` | `0` |
| `aider-shadow-cpp/skip-gap-calendar` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `1217` | `2` |
| `aider-shadow-cpp/snowplow-edge-router` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `2943` | `2` |
| `aider-shadow-cpp/status-panel-decimator` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `476` | `1` |
| `aider-shadow-cpp/time-parking-grace-audit` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `426` | `2` |
| `aider-shadow-cpp/timer-oven-safety-lock` | `-0.50` | `compilation_failure` | `yes` | `yes` | `0/0` | `no` | `254` | `567` | `2` |
| `aider-shadow-cpp/warranty-service-calendar` | `-0.80` | `fatal_parse_failure` | `no` | `no` | `0/0` | `no` | `` | `1296` | `0` |

## Notes

- `compilation_failure` contributed the largest total negative reward because it appeared in most assignments.
- `forbidden_file_or_primitive_violation` is the most negative per occurrence, but it only appeared 4 times.
- The monitor eval produced `0 / 32` all-tests-pass results in the final eval, so this report does not prove improvement over the SFT checkpoint. A separate fixed-26 eval receipt is still required for pass@1/pass@2 comparison.
- Full parsed reward rows are also saved in `docs/glm47-aider-ast17-grpo-035206-eval-rewards.json`.
