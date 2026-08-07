# GLM-4.7 Aider v3 530 GRPO Training Run Summary

This report records the recent GRPO run that continued from the reconstructed
SFT v3 complement-530 adapter. The fixed-26 benchmark result is included as the
external evaluation outcome for the final GRPO checkpoint.

## Run Identity

| Field | Value |
| --- | --- |
| GRPO run ID | `glm47-aider-v3-530-grpo-main-20260724-212514` |
| Stage | `GRPO` |
| Phase | `full` |
| Training gate status | `passed` |
| Source commit | `4c9d639c06666cd5f4f07c04265553a11eb4c8e7` |
| Training task count | `253` |
| Rollout updates | `26` |
| Official fixed-26 role | `external fixed evaluation only` |
| Run root | `/workspace/runs/glm47-aider-v3-530-grpo-main-20260724-212514` |
| Training data manifest | `/workspace/runs/glm47-aider-v3-530-grpo-main-20260724-212514/data/manifest.json` |
| Training data manifest SHA-256 | `d9a7f1f886e892478cd834decb7c396c4a86a1c3f712af4807b69e9aa5fc161d` |
| Data source tree SHA-256 | `a8bb8030f7ec287eee4f5c19146374d6722ec5af310cad632ed5938e7280f686` |

## Source SFT Adapter

| Field | Value |
| --- | --- |
| Source SFT run | `glm47-aider-complement-530-sft-20260721` |
| Raw SFT checkpoint | `iter_0000025` |
| Reconstructed SFT adapter used for GRPO | `/workspace/runs/glm47-aider-v3-530-sft-ep8-recon-20260724-212359/adapter` |
| Source adapter SHA-256 | `f1ea45bc327dc6e28d0287aea75c6b691e99d2ec2f7fdb7f07bbbf5ccd6cf36a` |
| Native reconstruction status | `passed` |
| Reconstruction target topology | `TP4 / EP8` |
| Source tensor count | `9741` |
| Layer 47 MTP tensor count | `207` |

## GRPO Training Configuration

| Setting | Value |
| --- | --- |
| Base model | `zai-org/GLM-4.7-Flash` |
| Model revision | `7dd20894a642a0aa287e9827cb1a1f7f91386b67` |
| LoRA rank / alpha | `16 / 32` |
| Tensor parallel size | `4` |
| Expert parallel size | `8` |
| GPUs per node | `8` |
| Rollout updates | `26` |
| Rollout batch size | `32` prompts |
| Samples per prompt | `8` |
| Global batch size | `256` |
| Sequence length | `6144` |
| Max response length | `4096` |
| Learning rate | `5e-7` |
| KL loss coefficient | `0.02` |
| Reward mode | `production_ast17` |
| Rollout temperature / top_p | `0.7 / 1.0` |

## Final GRPO Checkpoint

| Field | Value |
| --- | --- |
| Final checkpoint | `iter_0000025` |
| Final adapter path | `/workspace/runs/glm47-aider-v3-530-grpo-main-20260724-212514/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Eval-normalized adapter path | `/runs/glm47-aider-v3-530-grpo-main-20260724-212514/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Adapter model SHA-256 | `0304ec334c7b1b9b789d241bbd9f5ad69aa1b725002f1c1f21697b017bfc53b1` |
| Adapter config SHA-256 | `0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e` |
| Tensor count | `9741` |
| Layer 47 tensor count | `207` |
| Training state files | `8` |
| Hybrid manifest path | `/workspace/runs/glm47-aider-v3-530-grpo-main-20260724-212514/adapter_hybrid/mtp_strip_manifest.json` |
| Hybrid manifest SHA-256 | `b60106f0f5210a19a545f5fcc2509ac155834a1d14d4f1364b5a63097fdecef0` |

## Final Native Shards

| Native shard | SHA-256 |
| --- | --- |
| `adapter_megatron_tp0_pp0_ep0.pt` | `be2da53026e250ae3624565cd6096cb167395bfa22bf4c5d9e72fa7b3afd44c9` |
| `adapter_megatron_tp0_pp0_ep4.pt` | `f57be7b780ee961def1f5bcca21e2c6a7480a42b66e9c46691e0e5218b5d05c9` |
| `adapter_megatron_tp1_pp0_ep1.pt` | `d2ecebecfd4ebd0d426341d21fdbf768aa2ebc69c5155b418fde873428a311ce` |
| `adapter_megatron_tp1_pp0_ep5.pt` | `d34dcb4fd393b9d7cbb054282db07dd3ed1528749f58f1938dc71c4c5f811f5f` |
| `adapter_megatron_tp2_pp0_ep2.pt` | `54ef7a9eea772d4807e66b4d299a857e4bb1d8eca77d96e405280b9aa9d4b1b7` |
| `adapter_megatron_tp2_pp0_ep6.pt` | `45df634f43b452a693977d1912ebecbb15772bc880101afdc035603720ad0dd9` |
| `adapter_megatron_tp3_pp0_ep3.pt` | `f34a2bc46d1727d0b1d7e63844c150f97276f266f4c3b0b294c069b6cc50411d` |
| `adapter_megatron_tp3_pp0_ep7.pt` | `7ca7bd02e270f6d23722be1e1a33fa76b3a95cc6996cccdf020c10f7902f88a0` |

## Serving Conversion

| Field | Value |
| --- | --- |
| Conversion kind | `glm47-serving-adapter-conversion` |
| Source adapter path | `/runs/glm47-aider-v3-530-grpo-main-20260724-212514/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Source adapter SHA-256 | `0304ec334c7b1b9b789d241bbd9f5ad69aa1b725002f1c1f21697b017bfc53b1` |
| Serving adapter SHA-256 | `f5d38db50e2a8277633aa0e7a193127216d3d71685f5d2b4c9375116565acd92` |
| Source tensor count | `9741` |
| Removed layer 47 MTP tensors | `207` |
| Serving tensor count | `9534` |
| Training data manifest SHA-256 | `d9a7f1f886e892478cd834decb7c396c4a86a1c3f712af4807b69e9aa5fc161d` |

## Fixed-26 Eval Result

| Field | Value |
| --- | --- |
| Eval run ID | `glm47-aider-v3-530-grpo-main-20260724-212514-fixed26-eval` |
| Eval status | `complete` |
| Eval benchmark | `Aider Polyglot C++ fixed-26` |
| Eval model name | `openai/glm-4.7-flash-grpo` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| Polyglot commit | `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f` |
| Eval topology | `2 x TP4 shards on H100:4 each` |
| Tries | `2` |
| Threads per shard | `8` |
| Temperature / top_p | `0.7 / 1.0` |
| Started UTC | `2026-07-25T02:20:08.640822+00:00` |
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

## Fixed-26 Shard Breakdown

| Shard | Tasks | `pass@1` | `pass@2` / `pass_at_k` | Well-formed | Errors | Context exhausted | Seconds per case | Prompt tokens | Completion tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Shard 0 | `13` | `0` | `2` | `13` | `3` | `3` | `461.9` | `460,316` | `276,424` |
| Shard 1 | `13` | `0` | `4` | `13` | `1` | `1` | `484.3` | `893,099` | `316,432` |
| Total | `26` | `0` | `6` | `26` | `4` | `4` | - | `1,353,415` | `592,856` |

## Fixed-26 Task Split

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

## Interpretation

| Point | Detail |
| --- | --- |
| Training completion | The GRPO training gate passed, with all 26 rollout checkpoints preserved through `iter_0000025`. |
| Checkpoint integrity | The final adapter is SHA-bound and has the expected `9741` tensor source domain before serving conversion. |
| Eval quality | Fixed-26 `pass@2` reached `6 / 26`, but `pass@1` remained `0 / 26`. |
| Formatting | All 26 benchmark tasks were well formed, with no malformed responses. |
| Reliability | The run had `4` error outputs and `4` context exhaustions, both lower than the AST17 GRPO fixed-26 run recorded in the companion report. |
| Main weakness | All benchmark successes required the second try; no task was solved on the first attempt. |

