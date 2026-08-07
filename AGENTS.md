# Repository Agent Instructions

## Authority and required reading

This file governs the active `feature/aider-rl8-ast17-production-reward`
worktree. Before changing behavior, read these files completely:

1. `README.md`
2. `ROADMAP.md`
3. `docs/AIDER_SFT_SCOPE.md` for Aider task, dataset, evaluation, or training work
4. `.agents/skills/charm-skill/SKILL.md` and every routed reference for CHARM work
5. the relevant implementation and tests under `src/glm47_posttraining/` and
   `tests/`

Instructions imported from another branch are evidence only when their exact
source revision and bytes are recorded. They do not silently replace this
active-worktree contract.

## Active project

This branch implements GLM-4.7-Flash post-training with Miles on 8x H100 and
the associated Aider Polyglot C++ data, oracle, reward, evaluation, and
clean-room task-generation surfaces. Preserve the pinned model, dataset,
benchmark, image, tokenizer, and adapter identities documented in `README.md`.

The official fixed-26 Aider Polyglot C++ suite is evaluation-only. Never copy
its prompts, tests, reference code, API text, hidden behavior, or response
artifacts into positive training data.

## CHARM task generation

The exact trigger `Go for task generation V1` authorizes only the frozen
17-topic, three-tasks-per-topic, 51-task CHARM V1 workflow. Follow the ten
numbered steps in
`.agents/skills/charm-skill/references/task-generation-v1.md` in order.

Generation is forbidden until all pre-generation gates pass, including:

- the exact operator-supplied `updated task/audit-sft-data-quality/` tree;
- active failure evidence and previous-best attempt ledger by SHA-256;
- a complete 51-task curriculum and proposal plan;
- repository-wide exact, near, structural, and semantic uniqueness;
- one canonical append-only task-ID reservation registry and atomic lock;
- failure-conditioned synthesis authorization; and
- cumulative Generator Admission V4.1 `pre-generation` PASS.

Treat `dataset/tasks/` as canonical source and `dataset/jsonls/` as generated
projection. Repair owner-controlled generators and regenerate; never patch
generated tasks, JSONL, reports, or PASS receipts directly. Keep solutions,
tests, negative fixtures, receipts, and private `pre.jsonl` out of model-facing
and release payloads.

The V1 trigger authorizes generation, validation, owner remediation,
projection, and attempted SFT corpus admission. It does not authorize model
training, canary execution, checkpoint promotion, or deployment.

## Evidence and claims

Keep these statuses separate: failure evidence, generation admission, task
proof, independent audit, projection, dataset validation, curriculum
validation, training admission, corpus admission, canary, training dynamics,
consumer verification, promotion, and deployment certification.

Missing evidence is `not_completed`. A score, model-judge verdict, low loss,
or earlier-stage PASS cannot override a deterministic hard failure. Preserve
raw artifacts and bind every source, policy, task, row, and receipt by digest.

## Engineering rules

- Preserve user changes in a dirty worktree and avoid unrelated rewrites.
- Prefer repository-owned commands and deterministic, versioned JSON schemas.
- Keep C++ task prompts explicit about exact case-sensitive public APIs and
  editable files.
- Require strict C++17 warning-clean compilation, isolated public-header/API
  probes, deterministic oracles, GCC/Clang evidence where available, and
  ASan/UBSan plus applicable concurrency checks.
- Never expose secrets, private tests, hidden expected outputs, or evaluator
  internals to model-facing rows.
- Do not claim benchmark uplift without a matched, receipt-backed evaluation.

## Validation

Run checks proportional to the changed surface. The core local suite is:

```bash
python3 -m compileall src tests
python3 -m pytest -q
python3 .agents/skills/charm-skill/scripts/validate_generation_readiness.py --list-rules
python3 /home/ubuntu/.codex/skills/.system/skill-creator/scripts/quick_validate.py .agents/skills/charm-skill
```

For a CHARM protocol or reservation change, also run:

```bash
python3 -m pytest -q \
  tests/test_charm_generation_readiness.py \
  tests/test_charm_task_generation_v1_protocol.py \
  tests/test_charm_task_id_reservations.py
```
