# GLM-4.7 Aider Fixed-26 Eval Results

This report records fixed-26 Aider C++ evaluations for the AST17 SFT checkpoint
and two GRPO checkpoints. These are external fixed benchmark evaluations, not
the internal GRPO monitor evals from `train_monitor.jsonl`.

The AST17 SFT baseline and AST17 GRPO result are presented first, followed by
today's v3 GRPO result.

## Saved Result Summary

| Run family | Stage | Eval run ID | Checkpoint | `pass@1` | `pass@2` / `pass_at_k` | Well-formed | Error outputs | Context exhaustions |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| AST17 | SFT | `glm47-aider-ast17-sft1425-fixed26-eval-20260725-060721` | `iter_0000070` | `0 / 26` | `4 / 26` | `26 / 26` | `7` | `7` |
| AST17 | GRPO | `glm47-aider-ast17-grpo-main-20260724-035206-fixed26-eval-20260725-045938` | `iter_0000025` | `1 / 26` | `5 / 26` | `26 / 26` | `7` | `7` |
| v3 530 | GRPO | `glm47-aider-v3-530-grpo-main-20260724-212514-fixed26-eval` | `iter_0000025` | `0 / 26` | `6 / 26` | `26 / 26` | `4` | `4` |

## AST17 SFT Fixed-26 Eval

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-ast17-sft1425-fixed26-eval-20260725-060721` |
| Eval status | `complete` |
| SFT training run | `glm47-aider-ast17-sft1425-20260723-141256` |
| SFT checkpoint | `iter_0000070` |
| Adapter path | `/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Adapter SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| Serving adapter SHA-256 | `a4d31c61fa39ee723c01e12e82625c527c0b186c623b45c395b5cea51f61280f` |
| Training data manifest SHA-256 | `813637ced3078c661a857f7e858d43ab0390684366f41f68bbd6a703899f39a6` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot commit | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| Eval model name | `openai/glm-4.7-flash-grpo` |
| Edit format | `whole` |
| Language | `cpp` |
| Tries | `2` |
| Temperature / top_p | `0.7 / 1.0` |
| Completed UTC | `2026-07-25T04:39:53.490493+00:00` |

| Metric | Result |
| --- | ---: |
| Terminal tasks | `26` |
| Unique testcases | `26` |
| Terminal attempts | `52` |
| Maximum attempts | `52` |
| Short-circuited after first pass | `0` |
| `pass@1` | `0 / 26` = `0.0%` |
| `pass@2` / `pass_at_k` | `4 / 26` = `15.4%` |
| Well-formed tasks | `26 / 26` = `100.0%` |
| Malformed responses | `0` |
| Error outputs | `7` |
| Context exhaustions | `7` |
| Test timeouts | `0` |
| Prompt tokens | `1,426,604` |
| Completion tokens | `738,568` |

| Shard | Tasks | `pass@1` | `pass@2` / `pass_at_k` | Well-formed | Errors | Context exhausted | Prompt tokens | Completion tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Shard 0 | `13` | `0` | `1` | `13` | `4` | `4` | `942,013` | `408,377` |
| Shard 1 | `13` | `0` | `3` | `13` | `3` | `3` | `484,591` | `330,191` |
| Total | `26` | `0` | `4` | `26` | `7` | `7` | `1,426,604` | `738,568` |

### AST17 SFT Interpretation

The exact AST17 SFT checkpoint produced no first-try fixed-26 successes and four
total successes after two tries. The output format was clean across all 26
tasks, with no malformed responses and no test timeouts. The main failure
signals were 7 error outputs and 7 context exhaustions.

The `pass_at_k` field in the receipt is the fixed two-try Aider result for this
eval, so it is reported here as `pass@2`.

## AST17 GRPO Fixed-26 Eval

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-ast17-grpo-main-20260724-035206-fixed26-eval-20260725-045938` |
| Eval status | `complete` |
| GRPO training run | `glm47-aider-ast17-grpo-main-20260724-035206` |
| GRPO checkpoint | `iter_0000025` |
| Adapter path | `/runs/glm47-aider-ast17-grpo-main-20260724-035206/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Adapter SHA-256 | `aa75e8eaae36465b959de06286196e3cc9dd19c8d46d3cda8277fcaa05323c95` |
| Training data manifest SHA-256 | `b1533088916a0d795c55ec7ff7a1fa11de924ed7c0b38c88ff9f736b48f1ce9c` |
| Source SFT adapter | `/workspace/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Source SFT adapter SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot commit | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| Eval model name | `openai/glm-4.7-flash-grpo` |
| Edit format | `whole` |
| Language | `cpp` |
| Tries | `2` |
| Temperature / top_p | `0.7 / 1.0` |
| Completed UTC | `2026-07-25T03:26:41.840822+00:00` |

| Metric | Result |
| --- | ---: |
| Terminal tasks | `26` |
| Unique testcases | `26` |
| Terminal attempts | `51` |
| Maximum attempts | `52` |
| Short-circuited after first pass | `1` |
| `pass@1` | `1 / 26` = `3.8%` |
| `pass@2` / `pass_at_k` | `5 / 26` = `19.2%` |
| Well-formed tasks | `26 / 26` = `100.0%` |
| Malformed responses | `0` |
| Error outputs | `7` |
| Context exhaustions | `7` |
| Test timeouts | `0` |
| Prompt tokens | `1,015,829` |
| Completion tokens | `647,965` |

| Shard | Tasks | `pass@1` | `pass@2` / `pass_at_k` | Well-formed | Errors | Context exhausted | Seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Shard 0 | `13` | `1` | `3` | `13` | `3` | `3` | `509.6` |
| Shard 1 | `13` | `0` | `2` | `13` | `4` | `4` | `576.2` |
| Total | `26` | `1` | `5` | `26` | `7` | `7` | - |

### AST17 GRPO Interpretation

This run produced one first-try success and five total successes after two
tries. The output formatting was clean across all 26 tasks, with no malformed
responses and no test timeouts. The main weakness was still robustness under
long repair trajectories: 7 error outputs and 7 context exhaustions were
recorded.

The `pass_at_k` field in the receipt is the fixed two-try Aider result for this
eval, so it is reported here as `pass@2`.

## Fixed-26 Benchmark Tasks

All fixed-26 evaluations in this report used the same pinned Aider C++ benchmark
split. The tasks were not chosen ad hoc for any run; they are the fixed external
eval cases used by the Modal eval app.

| # | Task | Shard |
| ---: | --- | ---: |
| 1 | `all-your-base` | `0` |
| 2 | `allergies` | `0` |
| 3 | `bank-account` | `0` |
| 4 | `binary-search-tree` | `0` |
| 5 | `circular-buffer` | `0` |
| 6 | `clock` | `0` |
| 7 | `complex-numbers` | `0` |
| 8 | `crypto-square` | `0` |
| 9 | `diamond` | `0` |
| 10 | `dnd-character` | `0` |
| 11 | `gigasecond` | `0` |
| 12 | `grade-school` | `0` |
| 13 | `kindergarten-garden` | `0` |
| 14 | `knapsack` | `1` |
| 15 | `linked-list` | `1` |
| 16 | `meetup` | `1` |
| 17 | `parallel-letter-frequency` | `1` |
| 18 | `perfect-numbers` | `1` |
| 19 | `phone-number` | `1` |
| 20 | `queen-attack` | `1` |
| 21 | `robot-name` | `1` |
| 22 | `space-age` | `1` |
| 23 | `spiral-matrix` | `1` |
| 24 | `sublist` | `1` |
| 25 | `yacht` | `1` |
| 26 | `zebra-puzzle` | `1` |

## Today's v3 GRPO Fixed-26 Eval

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-v3-530-grpo-main-20260724-212514-fixed26-eval` |
| Eval status | `complete` |
| GRPO training run | `glm47-aider-v3-530-grpo-main-20260724-212514` |
| GRPO checkpoint | `iter_0000025` |
| Adapter path | `/runs/glm47-aider-v3-530-grpo-main-20260724-212514/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Adapter SHA-256 | `0304ec334c7b1b9b789d241bbd9f5ad69aa1b725002f1c1f21697b017bfc53b1` |
| Training data manifest SHA-256 | `d9a7f1f886e892478cd834decb7c396c4a86a1c3f712af4807b69e9aa5fc161d` |
| Source SFT adapter | `/workspace/runs/glm47-aider-v3-530-sft-ep8-recon-20260724-212359/adapter` |
| Source SFT adapter SHA-256 | `f1ea45bc327dc6e28d0287aea75c6b691e99d2ec2f7fdb7f07bbbf5ccd6cf36a` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot commit | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| Eval model name | `openai/glm-4.7-flash-grpo` |
| Edit format | `whole` |
| Language | `cpp` |
| Tries | `2` |
| Temperature / top_p | `0.7 / 1.0` |
| Completed UTC | `2026-07-25T02:41:49.124326+00:00` |

| Metric | Result |
| --- | ---: |
| Terminal tasks | `26` |
| Unique testcases | `26` |
| Terminal attempts | `52` |
| Maximum attempts | `52` |
| Short-circuited after first pass | `0` |
| `pass@1` | `0 / 26` = `0.0%` |
| `pass@2` / `pass_at_k` | `6 / 26` = `23.1%` |
| Well-formed tasks | `26 / 26` = `100.0%` |
| Malformed responses | `0` |
| Error outputs | `4` |
| Context exhaustions | `4` |
| Test timeouts | `0` |
| Prompt tokens | `1,353,415` |
| Completion tokens | `592,856` |

| Shard | Tasks | `pass@1` | `pass@2` / `pass_at_k` | Well-formed | Errors | Context exhausted | Seconds per case |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Shard 0 | `13` | `0` | `2` | `13` | `3` | `3` | `461.9` |
| Shard 1 | `13` | `0` | `4` | `13` | `1` | `1` | `484.3` |
| Total | `26` | `0` | `6` | `26` | `4` | `4` | - |

### Today's v3 GRPO Interpretation

This run produced no first-try successes and six total successes after two
tries. The output format remained clean on all 26 tasks, and the run had no
malformed responses or test timeouts. The stronger signs are low absolute error
outputs and context exhaustions for a two-try fixed-26 run, but the absence of
first-try passes means the model still relies on the repair attempt for every
fixed-26 success.

The `pass_at_k` field in the receipt is the fixed two-try Aider result for this
eval, so it is reported here as `pass@2`.
