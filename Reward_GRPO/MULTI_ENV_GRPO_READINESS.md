# Multi-environment GRPO readiness

Status: **STATICALLY READY; POST-MERGE DOCKER CANARY PENDING**

- Warm start: `phone-number-kernel12-grpo20-spot-20260822-102653`, checkpoint `iter_0000014`.
- Adapter SHA-256: `62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a`.
- Dataset: 17 official C++ topics expanded into 73 policy environments: 13 task-specific topics and four topics using the global C++ verifier.
- Prompts: original Polyglot instructions and starter files from commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; policy IDs remain metadata-only.
- Reward: selected live policy plus its report-required terminal policies, executed through the existing verifier scripts in a network-disabled GCC 13.3 container. INVALID results are group-neutralized.
- Final-package routing: Clock E06 and Crypto Square E06 are their official terminal policies; Diamond retains E05+E06; Kindergarten Garden now uses its six task-specific policies with E06 terminal.
- Training controls: 30 updates, rollout batch 8, 32 samples per prompt, global batch 256, thinking enabled, TP4/EP8 on 8 H100s.
- Static preflight: 17 topics, 73 train rows, 17 monitor rows, unique verifier discovery, and policy/prompt isolation passed.
- Static config SHA-256: `4442166f0cba268b09700db06474824d2b1bc47b0bddd2754815ea0944b70df6`.
- Focused tests: 5/5 passed.
- Extra assets retained intentionally: the Phone Number warm-start environment and Crypto Square post-training evaluation harness. Bank Account and D&D Character verifier packages are outside this 17-topic curriculum.

The launch YAML performs the static gate during setup and builds the pinned verifier container before training. A fresh known-good Docker canary must still pass after the image is built; the static checks do not prove container execution or a distributed reward-worker run.
