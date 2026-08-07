# GLM-4.7 Aider AST17 And July 24 Fixed-26 Eval Summary

This report separates the exact AST17 SFT fixed-26 result, the AST17 GRPO
fixed-26 result, and the July 24 v3 530 GRPO fixed-26 result. For all fixed-26
rows, `pass_at_k` is reported as `pass@2` because the eval uses two tries.

## AST17 SFT Fixed-26 Eval

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-ast17-sft1425-fixed26-eval-20260725-060721` |
| Eval status | `complete` |
| SFT training run | `glm47-aider-ast17-sft1425-20260723-141256` |
| SFT checkpoint | `iter_0000070` |
| Adapter SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| `pass@1` | `0 / 26` = `0.0%` |
| `pass@2` / `pass_at_k` | `4 / 26` = `15.4%` |
| Well-formed tasks | `26 / 26` = `100.0%` |
| Malformed responses | `0` |
| Error outputs | `7` |
| Context exhaustions | `7` |
| Test timeouts | `0` |

## AST17 SFT Interpretation

| Point | Detail |
| --- | --- |
| First-try quality | The exact AST17 SFT checkpoint produced no first-try fixed-26 successes. |
| Two-try quality | It produced four total successes after two tries. |
| Formatting | Output format was clean across all 26 tasks, with no malformed responses. |
| Stability | No test timeouts were recorded. |
| Main failure signals | `7` error outputs and `7` context exhaustions. |
| Metric note | `pass_at_k` is the fixed two-try Aider result, so it is reported as `pass@2`. |

## AST17 GRPO Fixed-26 Eval

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-ast17-grpo-main-20260724-035206-fixed26-eval-20260725-045938` |
| Eval status | `complete` |
| GRPO training run | `glm47-aider-ast17-grpo-main-20260724-035206` |
| GRPO checkpoint | `iter_0000025` |
| Adapter SHA-256 | `aa75e8eaae36465b959de06286196e3cc9dd19c8d46d3cda8277fcaa05323c95` |
| `pass@1` | `1 / 26` = `3.8%` |
| `pass@2` / `pass_at_k` | `5 / 26` = `19.2%` |
| Well-formed tasks | `26 / 26` = `100.0%` |
| Malformed responses | `0` |
| Error outputs | `7` |
| Context exhaustions | `7` |
| Test timeouts | `0` |

## AST17 GRPO Interpretation

| Point | Detail |
| --- | --- |
| First-try quality | This run produced one first-try success. |
| Two-try quality | It produced five total successes after two tries. |
| Formatting | Output formatting was clean across all 26 tasks, with no malformed responses. |
| Stability | No test timeouts were recorded. |
| Main weakness | Robustness under long repair trajectories remained weak: `7` error outputs and `7` context exhaustions were recorded. |
| Metric note | `pass_at_k` is the fixed two-try Aider result, so it is reported as `pass@2`. |

## AST17 SFT To GRPO Comparison

| Metric | AST17 SFT | AST17 GRPO | GRPO Delta |
| --- | ---: | ---: | ---: |
| `pass@1` | `0 / 26` = `0.0%` | `1 / 26` = `3.8%` | `+1` task, `+3.8 pp` |
| `pass@2` / `pass_at_k` | `4 / 26` = `15.4%` | `5 / 26` = `19.2%` | `+1` task, `+3.8 pp` |
| Well-formed tasks | `26 / 26` = `100.0%` | `26 / 26` = `100.0%` | `0` |
| Malformed responses | `0` | `0` | `0` |
| Error outputs | `7` | `7` | `0` |
| Context exhaustions | `7` | `7` | `0` |
| Test timeouts | `0` | `0` | `0` |

## July 24 v3 530 GRPO Run Details

| Field | Value |
| --- | --- |
| GRPO training run | `glm47-aider-v3-530-grpo-main-20260724-212514` |
| Eval run ID | `glm47-aider-v3-530-grpo-main-20260724-212514-fixed26-eval` |
| Eval status | `complete` |
| GRPO checkpoint | `iter_0000025` |
| Adapter SHA-256 | `0304ec334c7b1b9b789d241bbd9f5ad69aa1b725002f1c1f21697b017bfc53b1` |
| Training data manifest SHA-256 | `d9a7f1f886e892478cd834decb7c396c4a86a1c3f712af4807b69e9aa5fc161d` |
| Source SFT adapter SHA-256 | `f1ea45bc327dc6e28d0287aea75c6b691e99d2ec2f7fdb7f07bbbf5ccd6cf36a` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot commit | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| Eval completed UTC | `2026-07-25T02:41:49.124326+00:00` |

### Table 1: Evaluation Metrics

| Metric | Result | Meaning |
| --- | ---: | --- |
| `pass@1` | `0 / 26` = `0.0%` | No task passed on the first attempt. |
| `pass@2` / `pass_at_k` | `6 / 26` = `23.1%` | Six tasks passed within two attempts. |
| First-try-only wins | `0` | There were no immediate successes. |
| Second-try recovery wins | `6` | All successful tasks required the repair attempt. |
| Failed after both tries | `20 / 26` = `76.9%` | These tasks did not pass after two attempts. |
| Well-formed tasks | `26 / 26` = `100.0%` | Output format was valid for every benchmark task. |
| Malformed responses | `0` | No benchmark result failed due to malformed response format. |
| Error outputs | `4` | Four tasks emitted error outputs during eval. |
| Context exhaustions | `4` | Four tasks exhausted context during repair/eval. |
| Test timeouts | `0` | No task failed due to test timeout. |

### Table 2: Shard Performance Breakdown

| Shard | Task count | `pass@1` | `pass@2` | Failed after both tries | Error outputs | Context exhausted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Shard 0 | `13` | `0` | `2` | `11` | `3` | `3` |
| Shard 1 | `13` | `0` | `4` | `9` | `1` | `1` |
| Total | `26` | `0` | `6` | `20` | `4` | `4` |

## Base, SFT v3, And July 24 GRPO Comparison

| Field | Base | SFT v3 | July 24 GRPO |
| --- | ---: | ---: | ---: |
| `pass@1` | `0 / 26` = `0.0%` | `0 / 26` = `0.0%` | `0 / 26` = `0.0%` |
| `pass@2` / `pass_at_k` | `4 / 26` = `15.4%` | `7 / 26` = `26.9%` | `6 / 26` = `23.1%` |
| `pass@2` delta vs Base | - | `+3` tasks, `+11.5 pp` | `+2` tasks, `+7.7 pp` |
| `pass@2` delta vs SFT v3 | - | - | `-1` task, `-3.8 pp` |

## Summary

| Point | Detail |
| --- | --- |
| AST17 GRPO vs AST17 SFT | AST17 GRPO improved by one task on both `pass@1` and `pass@2`, but kept the same error-output and context-exhaustion counts. |
| July 24 GRPO absolute quality | July 24 GRPO reached `6 / 26` on `pass@2`, but still had `0 / 26` on `pass@1`. |
| July 24 GRPO vs SFT v3 | July 24 GRPO underperformed SFT v3 by one `pass@2` task: `6 / 26` vs `7 / 26`. |
| Important correction | `6 / 26` is `23.1%`; `-3.8 pp` is the delta versus SFT v3, not the absolute GRPO percentage. |

