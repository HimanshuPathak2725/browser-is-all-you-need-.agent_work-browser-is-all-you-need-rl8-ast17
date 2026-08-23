# Multi-environment GRPO readiness

Status: **READY TO LAUNCH**

- Warm start: `phone-number-kernel12-grpo20-spot-20260822-102653`, checkpoint `iter_0000014`.
- Adapter SHA-256: `62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a`.
- Dataset: 12 official C++ topics expanded into 62 validated policy environments.
- Prompts: original Polyglot instructions and starter files from commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`; policy IDs remain metadata-only.
- Reward: selected live policy plus its report-required terminal policies, executed through the existing verifier scripts in a network-disabled GCC 13.3 container. INVALID results are group-neutralized.
- Training controls: unchanged from the successful Phone Number template—20 updates, rollout batch 8, 32 samples per prompt, global batch 256, thinking enabled, TP4/EP8 on 8 H100s.
- Static preflight: 12 topics, 62 train rows, 12 monitor rows, policy/prompt isolation passed.
- Focused tests: 5/5 passed.

The launch YAML performs the fast static gate during setup and builds the pinned verifier container before training. It does not rerun the full validation corpus.
