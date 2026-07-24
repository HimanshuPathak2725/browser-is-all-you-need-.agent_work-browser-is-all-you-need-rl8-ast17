# GLM-4.7 Aider AST17 GRPO Training Performance

This note records the completed GRPO training run that continued from the
selected SFT checkpoint. It summarizes the training health metrics and the
per-update reward/eval chart from the final `run.log`.

## Run Identity

| Field | Value |
| --- | --- |
| GRPO run ID | `glm47-aider-ast17-grpo-main-20260724-035206` |
| Run status | `success` |
| Ray status | `0` |
| Training gate status | `passed` |
| Training gate file | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/grpo_lora_r16/grpo_training_gate.json` |
| Final checkpoint iteration | `iter_0000025` |
| Final adapter path | `/workspace/runs/glm47-aider-ast17-grpo-main-20260724-035206/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Eval-normalized adapter path | `/runs/glm47-aider-ast17-grpo-main-20260724-035206/checkpoints/grpo_lora_r16/iter_0000025/adapter` |
| Final `adapter_model.bin` SHA-256 | `aa75e8eaae36465b959de06286196e3cc9dd19c8d46d3cda8277fcaa05323c95` |
| Adapter config SHA-256 | `0bd6d85f88fc42fefa52627b3c261f1ad58bb2c9519332ae8034dd5dffe2498e` |
| Source SFT adapter | `/workspace/runs/glm47-aider-ast17-sft1425-20260723-141256/checkpoints/sft_lora_r16/iter_0000070/adapter` |
| Source SFT adapter SHA-256 | `2b118e4cf3a52917fa70c3a86124d8e75b1ff7c0ea40f02f1f17b104dbd7f5af` |
| Data manifest SHA-256 | `b1533088916a0d795c55ec7ff7a1fa11de924ed7c0b38c88ff9f736b48f1ce9c` |
| Dataset kind | `aider-polyglot-cpp-shadow-grpo` |
| Training task count | `253` |
| Rollout updates | `26` |
| Rollout batch size | `32` |
| Samples per prompt | `8` |
| Global batch size | `256` |
| KL loss coefficient | `0.02` |
| LoRA rank / alpha | `16 / 32` |
| Wall time | `9511 s` (~2h 38m) |
| Peak GPU memory | `69189 MiB` |
| W&B run | `https://wandb.ai/sparmar27feb2003-nit-kurukshetra/glm47-aider-polyglot-cpp-grpo/runs/glm47-aider-ast17-grpo-main-20260724-035206` |

## Training Performance Summary

| Metric | First | Best / Min | Final | Mean | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Train loss | `-0.000000` @ step 0 | min `-0.000000` @ step 0 | `0.000204` @ step 25 | `0.000172` | Small and stable; mostly KL-driven rather than SFT-style cross-entropy. |
| KL loss | `-0.000000` @ step 0 | max `0.010192` @ step 25 | `0.010192` @ step 25 | `0.008597` | Controlled policy drift; final KL is still small. |
| Raw rollout reward | `-0.564453` @ rollout 0 | best `-0.533203` @ rollout 20 | `-0.553125` @ rollout 25 | `-0.549594` | Mild, noisy reward lift; final is better than start but below the best checkpoint. |
| Monitor eval reward | `-0.546875` @ eval 0 | best `-0.509375` @ eval 15 | `-0.537500` @ eval 25 | `-0.540625` | Small monitor improvement, noisy and not a held-out fixed-26 result. |
| Passrate | `0.0` | `0.0` | `0.0` | `0.0` | No pass@k lift was visible in the training-loop passrate logs. |

## Per-Update Training Chart

Each row is one GRPO update. Higher reward/eval reward is better because the
values are negative. `pass@k` comes from the training-loop passrate logger, not
the final fixed-26 evaluation.

| Update | Train loss | PG loss | KL loss | Rollout KL | Grad norm | Raw reward | Monitor eval | Pass@1 | Pass@2 | Rollout trunc. | Eval trunc. | Mean resp. len |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | -0.000000 | -0.00000003 | -0.000000 | 0.028953 | 0.198438 | -0.564453 | -0.546875 | 0.0 | 0.0 | 0.035156 | 0.000000 | 1003.50 |
| 1 | 0.000178 | -0.00000002 | 0.008895 | 0.031871 | 0.139326 | -0.560937 | -0.546875 | 0.0 | 0.0 | 0.046875 | 0.062500 | 1056.89 |
| 2 | 0.000192 | -0.00000004 | 0.009614 | 0.033312 | 0.315377 | -0.565625 | -0.540625 | 0.0 | 0.0 | 0.054688 | 0.000000 | 1081.13 |
| 3 | 0.000178 | -0.00000005 | 0.008899 | 0.029456 | 0.195611 | -0.553125 | -0.556250 | 0.0 | 0.0 | 0.046875 | 0.062500 | 1140.01 |
| 4 | 0.000174 | -0.00000004 | 0.008714 | 0.028611 | 0.204130 | -0.554297 | -0.528125 | 0.0 | 0.0 | 0.066406 | 0.031250 | 1152.25 |
| 5 | 0.000174 | -0.00000007 | 0.008696 | 0.030588 | 0.214663 | -0.551562 | -0.537500 | 0.0 | 0.0 | 0.066406 | 0.093750 | 1039.05 |
| 6 | 0.000168 | -0.00000003 | 0.008403 | 0.028922 | 0.158054 | -0.551953 | -0.537500 | 0.0 | 0.0 | 0.046875 | 0.000000 | 1113.04 |
| 7 | 0.000169 | -0.00000005 | 0.008442 | 0.029305 | 0.234427 | -0.546484 | -0.546875 | 0.0 | 0.0 | 0.031250 | 0.062500 | 1062.32 |
| 8 | 0.000191 | -0.00000002 | 0.009561 | 0.032670 | 0.181334 | -0.555078 | -0.537500 | 0.0 | 0.0 | 0.031250 | 0.000000 | 1001.72 |
| 9 | 0.000177 | -0.00000006 | 0.008860 | 0.029119 | 0.712233 | -0.542969 | -0.565625 | 0.0 | 0.0 | 0.042969 | 0.031250 | 1028.66 |
| 10 | 0.000168 | -0.00000004 | 0.008400 | 0.030484 | 0.231852 | -0.547266 | -0.518750 | 0.0 | 0.0 | 0.019531 | 0.062500 | 987.57 |
| 11 | 0.000178 | -0.00000006 | 0.008898 | 0.029260 | 0.203405 | -0.556250 | -0.528125 | 0.0 | 0.0 | 0.042969 | 0.031250 | 1114.19 |
| 12 | 0.000192 | -0.00000005 | 0.009614 | 0.029949 | 0.390758 | -0.555469 | -0.537500 | 0.0 | 0.0 | 0.054688 | 0.062500 | 1135.36 |
| 13 | 0.000161 | -0.00000004 | 0.008045 | 0.028782 | 0.163523 | -0.535156 | -0.565625 | 0.0 | 0.0 | 0.039062 | 0.062500 | 1023.13 |
| 14 | 0.000179 | -0.00000004 | 0.008977 | 0.029891 | 0.147661 | -0.541797 | -0.584375 | 0.0 | 0.0 | 0.027344 | 0.125000 | 1008.94 |
| 15 | 0.000173 | -0.00000007 | 0.008659 | 0.030042 | 0.170677 | -0.542969 | -0.509375 | 0.0 | 0.0 | 0.027344 | 0.000000 | 937.32 |
| 16 | 0.000187 | -0.00000002 | 0.009376 | 0.028139 | 0.212131 | -0.544531 | -0.528125 | 0.0 | 0.0 | 0.035156 | 0.000000 | 1200.84 |
| 17 | 0.000171 | -0.00000006 | 0.008536 | 0.030115 | 0.248149 | -0.551953 | -0.562500 | 0.0 | 0.0 | 0.039062 | 0.093750 | 949.33 |
| 18 | 0.000176 | -0.00000006 | 0.008806 | 0.030094 | 0.160489 | -0.542578 | -0.537500 | 0.0 | 0.0 | 0.046875 | 0.031250 | 1072.00 |
| 19 | 0.000170 | -0.00000005 | 0.008507 | 0.027894 | 0.231905 | -0.542578 | -0.528125 | 0.0 | 0.0 | 0.027344 | 0.031250 | 1007.52 |
| 20 | 0.000169 | -0.00000001 | 0.008457 | 0.028297 | 0.126008 | -0.533203 | -0.565625 | 0.0 | 0.0 | 0.035156 | 0.062500 | 1015.55 |
| 21 | 0.000177 | -0.00000005 | 0.008876 | 0.029377 | 0.187515 | -0.558594 | -0.537500 | 0.0 | 0.0 | 0.070312 | 0.062500 | 1282.20 |
| 22 | 0.000191 | -0.00000003 | 0.009571 | 0.031639 | 0.186293 | -0.552344 | -0.509375 | 0.0 | 0.0 | 0.039062 | 0.000000 | 949.10 |
| 23 | 0.000170 | -0.00000005 | 0.008526 | 0.028085 | 0.144828 | -0.545312 | -0.537500 | 0.0 | 0.0 | 0.058594 | 0.031250 | 1220.02 |
| 24 | 0.000200 | -0.00000004 | 0.009987 | 0.030768 | 0.220099 | -0.539844 | -0.525000 | 0.0 | 0.0 | 0.019531 | 0.000000 | 894.05 |
| 25 | 0.000204 | -0.00000003 | 0.010192 | 0.031950 | 0.204659 | -0.553125 | -0.537500 | 0.0 | 0.0 | 0.054688 | 0.031250 | 1125.18 |

## Key Observations

- The run completed successfully and produced a gated final adapter at `iter_0000025`.
- Training was numerically stable: gradient norms stayed finite, KL stayed near `0.008` to `0.010`, and the final loss remained around `2e-4`.
- The best training reward occurred at rollout `20` (`-0.533203`), while the final rollout was `-0.553125`; this is a small positive shift from the start but not monotonic.
- The best monitor eval reward occurred at eval `15` and again at eval `22` (`-0.509375`); the final monitor eval was `-0.537500`.
- Passrate remained `0.0` in the training-loop logger, so this run does not yet prove task-level improvement over SFT.

## Evaluation Status

This document is a training-performance record. The fixed-26 evaluation should
be run separately using the final checkpoint from `grpo_training_gate.json`
before claiming an improvement over SFT.
