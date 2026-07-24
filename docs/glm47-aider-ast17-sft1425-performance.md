# GLM-4.7 Aider AST17 SFT1425 Checkpoint Performance

This note records the supervised fine-tuning checkpoint selected as the
starting adapter for the AST17 GRPO run. The checkpoint is:

```text
glm47-runs:/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter
```

The local evidence set contains training-loop metrics for the exact SFT run and
GRPO adapter-preparation provenance for the exact checkpoint. It does not
contain an exact fixed-26 Aider evaluation receipt for this SFT run. A separate
fixed-26 SFT evaluation receipt exists for a different `expansion-sft` run and
is listed only as adjacent evidence.

## Checkpoint Selected For GRPO

| Field | Value |
| --- | --- |
| SFT run ID | `glm47-aider-ast17-sft1425-20260723-141256` |
| Selected SFT iteration | `iter_0000070` |
| Modal volume checkpoint | `glm47-runs:/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| In-container checkpoint | `/workspace/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Current GRPO run using it | `glm47-aider-ast17-grpo-main-20260723-152812` |
| GRPO hybrid adapter path | `/workspace/runs/glm47-aider-ast17-grpo-main-20260723-152812/adapter_hybrid` |
| Base HF checkpoint | `/root/models/GLM-4.7-Flash` |
| Megatron load checkpoint | `/root/models/GLM-4.7-Flash_torch_dist_tp4_pp1_ep8` |
| W&B project | `glm47-pie-cpp-posttraining` |
| W&B run | `https://wandb.ai/sparmar27feb2003-nit-kurukshetra/glm47-pie-cpp-posttraining/runs/glm47-aider-ast17-sft1425-20260723-141256` |

## Dataset Identity

| Field | Value |
| --- | ---: |
| Packaged SFT rows | `1425` |
| SFT rows consumed/logged by run | `1420` |
| SFT train JSONL SHA-256 | `ea0dd7e399dfb27f154ce1c619c696f526a536bbde6dca78c665d78bdeef4b78` |
| Imported data manifest SHA-256 | `813637ced3078c661a857f7e858d43ab0390684366f41f68bbd6a703899f39a6` |
| Source SFT JSONL | `/data/Tirtha/browser-is-all-you-need/.glm47-posttraining/data/aider_tasks/sft/train.jsonl` |
| Local imported data root | `.glm47-posttraining/imported_aider_data_sft1425` |
| Manifest kind | `local-self-contained-aider-polyglot-cpp-dataset` |
| Manifest note | SFT train split uses the 1425-row local Aider JSONL; GRPO/eval descriptors remain the imported 20/6 smoke split. |
| Manifest SFT count | `1425` |
| Manifest GRPO smoke count | `20` |
| Manifest validation count | `6` |

The SFT run used `sft/train.jsonl`. The `grpo/train.jsonl` and
`eval/validation.jsonl` files in the same imported data root are smoke/eval
material from the importer and are not the 1425-row SFT supervision stream.

## Training Configuration

| Setting | Value |
| --- | --- |
| Stage | SFT LoRA |
| Training module | `glm47_posttraining.integrations.miles_train_with_glm47_bridge` |
| Rollout function | `miles.rollout.sft_rollout.generate_rollout` |
| Epochs | `1` |
| Rollout batch size | `20` |
| Global batch size | `20` |
| Micro batch size | `1` |
| Sequence length | `3072` |
| Max tokens per GPU | `16384` |
| Optimizer | Adam |
| LR schedule | cosine |
| LR range | `1e-5` peak to `1e-6` minimum/final |
| Weight decay | `0.1` |
| Adam betas | `0.9`, `0.95` |
| LoRA rank | `16` |
| LoRA alpha | `32` |
| LoRA dropout | `0.0` |
| LoRA target modules | `q_a_proj`, `kv_a_proj_with_mqa`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Shared expert LoRA layout | `--experts-shared-outer-loras` |
| SGLang LoRA backend | `triton` |
| SGLang DP attention | enabled, `dp_size=8` |
| Parallelism | world size `8`, data parallel `2`, tensor parallel `4`, pipeline parallel `1`, context parallel `1`, expert parallel `8` |
| Hardware | 8x NVIDIA H100 80GB; NVLink not detected in run header |

## SFT Training Performance

| Metric | Value | Notes |
| --- | ---: | --- |
| Run status | `success` | Ray job `raysubmit_S9xP1XgXjBqQpcnZ` succeeded. |
| Wall time | `1229 s` | 20 min 29 s from wrapper receipt. |
| Update steps | `71` | Logged steps `0` through `70`; final checkpoint is `iter_0000070`. |
| Checkpoint cadence | every step | `--save-interval 1` |
| Rollout rows logged | `1420` | W&B evidence summary and 71 batches x 20 samples. |
| Eval rows logged | `0` | No SFT eval rows were logged in this run. |
| Peak GPU memory | `72363 MiB` | From `vram_peak.txt`. |
| First train loss | `0.403495` | Step `0`. |
| Final train loss | `0.156413` | Step `70`; also the minimum logged loss. |
| Loss reduction | `61.2%` | Step `0` to step `70`. |
| Mean train loss | `0.286823` | Across 71 logged steps. |
| Median train loss | `0.279888` | Across 71 logged steps. |
| First grad norm | `0.703228` | Step `0`. |
| Final grad norm | `0.194224` | Step `70`. |
| Mean grad norm | `0.416194` | Max logged grad norm was `3.211251`. |
| Final LR | `1e-6` | `train/lr-pg_0` and `train/lr-pg_1`. |
| Truncation ratio | `0.0` | No rollout truncation observed in logged SFT batches. |
| Mean rollout response length | `824.45` tokens | Final batch mean was `842.15`. |
| Mean rollout time | `1.342 s` | Steady-state steps `1..70`; step `0` excluded as startup. |
| Mean rollout throughput | `1537.12` tokens/GPU/s | Steady-state steps `1..70`; final batch was `1562.30`. |
| Mean actor train time | `4.044 s` | Steady-state steps `1..70`. |
| Mean actor train throughput | `8078.16` tokens/s | Steady-state steps `1..70`; final batch was `7073.29`. |
| Mean actor train TFLOP/s | `22.627` | Steady-state steps `1..70`; final batch was `20.439`. |
| Mean step time | `12.310 s` | Steady-state steps `1..70`; final batch was `13.500`. |
| Mean wait-time ratio | `0.674` | Steady-state steps `1..70`. |

Training-loop interpretation: optimization completed cleanly, loss fell
substantially, gradients stayed finite, no rollout truncation was logged, and
the selected checkpoint was saved as both native Megatron LoRA shards and an HF
PEFT adapter. These are training-health metrics, not held-out model-quality
metrics.

## Checkpoint Integrity And GRPO Preparation

| Field | Value |
| --- | --- |
| Source adapter path in GRPO prep manifest | `/__modal/volumes/vo-zTfY4cHVssD7FbUXZOrCKf/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Source `adapter_model.bin` SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| Source `adapter_config.json` SHA-256 | `0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e` |
| Source tensor count | `9741` |
| Stripped tensor count | `207` |
| Kept tensor count | `9534` |
| Stripped tensor region | Layer `47` MTP tensors |
| First stripped tensor | `model.layers.47.mlp.experts.gate_proj.lora_A.weight` |
| Hybrid `adapter_model.bin` SHA-256 | `a4d31c61fa39ee723c01e12e82625c527c0b186c623b45c395b5cea51f61280f` |
| Native shard count | `8` |
| Training-state files in hybrid manifest | none |

Native shard hashes prepared for GRPO:

| Native shard | SHA-256 |
| --- | --- |
| `adapter_megatron_tp0_pp0_ep0.pt` | `dadbef30872cbbcac722e448e51bf5263f63bc2e26204ad700ff87ceeaa99c93` |
| `adapter_megatron_tp0_pp0_ep4.pt` | `50138edd2f6867e5699a6cb57d4ac92d8e78de7dcdf43a1c80ec8ad690516820` |
| `adapter_megatron_tp1_pp0_ep1.pt` | `eddc54ac1e8ed3dcc6d5c3ece55897ad0688a5ee61abcd990a4967c829d1e239` |
| `adapter_megatron_tp1_pp0_ep5.pt` | `67084483abdd79abc5d209638b3480bfe661c15ac6510f3cb9d938ed161a5ecc` |
| `adapter_megatron_tp2_pp0_ep2.pt` | `9e044a16c8cdea22aa1ac7ae31939ca0864894ceb65782ce0ff17f77ac9f8c22` |
| `adapter_megatron_tp2_pp0_ep6.pt` | `372c79929dad9d81e395273fb46eab438b0bf4fe2e6dcd577bdaf87e617dd66a` |
| `adapter_megatron_tp3_pp0_ep3.pt` | `4eb8a3363d65b39114575143e55aaa75542217045ee6fa6ae1d16a671e57f822` |
| `adapter_megatron_tp3_pp0_ep7.pt` | `f433f4d3176017bbd2fa71d06b2b52ca9f3eafbdab769b52256e2dc04020de24` |

The current GRPO launch used the prepared hybrid adapter:

```text
--lora-adapter-path /workspace/runs/glm47-aider-ast17-grpo-main-20260723-152812/adapter_hybrid
```

The same GRPO log shows `kept 9534/9741 tensors (stripped 207 MTP tensors)`
before reporting `HYBRID_ADAPTER_READY`.

## Fixed-26 Evaluation Status

| Evaluation evidence | Applies to exact AST17 SFT checkpoint? | Result |
| --- | --- | --- |
| Exact fixed-26 receipt for `glm47-aider-ast17-sft1425-20260723-141256` | No local receipt found | Not measured in the evidence set. |
| Adjacent fixed-26 SFT receipt `/tmp/aider_sft_run_receipt.json` | No. It points to `/runs/glm47-aider-expansion-sft-20260723T074257Z/checkpoints/sft_lora_r16/iter_0000070/adapter`. | Pass@1 `0/26`, Pass@2 `3/26`, well formed `26/26`, malformed `0`, context exhaustions `9`, error outputs `9`, timeout `1`. |

Do not use the adjacent `expansion-sft` receipt as the quality metric for the
`ast17-sft1425` checkpoint unless the two checkpoint directories are separately
proven byte-identical. The adapter config hash matches the AST17 source config
hash, but the recorded exact source paths and adapter hashes differ.

## Evidence Files Used

| Evidence file | SHA-256 | Purpose |
| --- | --- | --- |
| `/tmp/sft1425_run.log` | `b5734c856df7f8b638e317e856eab9a802f51fdf261bb37bd72a5dad63e752b7` | Exact SFT training log and W&B finalization output. |
| `/tmp/sft1425_vram_peak.txt` | `f19896500deb0702f5503142c016ae355a9b89dcfcd3598677d654e59b7cb596` | Peak GPU memory evidence. |
| `.glm47-posttraining/imported_aider_data_sft1425/manifest.json` | `813637ced3078c661a857f7e858d43ab0390684366f41f68bbd6a703899f39a6` | Imported data manifest. |
| `.glm47-posttraining/imported_aider_data_sft1425/sft/train.jsonl` | `ea0dd7e399dfb27f154ce1c619c696f526a536bbde6dca78c665d78bdeef4b78` | 1425-row SFT supervision file. |
| `/tmp/current_grpo_mtp_strip_manifest.json` | `8e3b7dbfbc21bb0dc5e4a87b89d1f33a0e357b33067493265214529bbf6e93ec` | Source checkpoint tensor identity and GRPO hybrid adapter preparation. |
| `/tmp/current_grpo_data_manifest.json` | `2cfa8a6cd27d513d69152f0c1cd2da3a555c0663bbca7210eaa4f966744f3270` | Current GRPO data identity. |
| `/tmp/current_grpo_logs_estimate.txt` | `acbef4900682553a1c257e28812f9b2d466b8efa13bab2e3be5bee21b552326e` | GRPO launch header confirming the hybrid adapter was used. |

## Recheck Commands

```bash
SFT_RUN_ID="glm47-aider-ast17-sft1425-20260723-141256"
SFT_ITER="iter_0000070"
SFT_ADAPTER="/workspace/runs/$SFT_RUN_ID/checkpoints/sft_lora_r16/$SFT_ITER/adapter"

modal volume ls glm47-runs \
  "$SFT_RUN_ID/checkpoints/sft_lora_r16/$SFT_ITER/adapter"
```

For promotion-quality comparison, run a fixed-26 Aider C++ evaluation against
the exact `ast17-sft1425` checkpoint and record its Pass@1, Pass@2, malformed
response count, context exhaustion count, and artifact hashes in a durable
receipt under `docs/receipts/`.
