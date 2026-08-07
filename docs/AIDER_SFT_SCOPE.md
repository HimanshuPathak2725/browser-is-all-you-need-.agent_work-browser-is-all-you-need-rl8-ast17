# Active Aider C++ SFT Scope

## Authority

This document defines Aider C++ task and dataset scope for the active
`feature/aider-rl8-ast17-production-reward` worktree. It supplements
`AGENTS.md`, `README.md`, and the CHARM V1 protocol. It does not declare a
dataset release, training run, checkpoint improvement, or deployment approval.

## Existing evaluation boundary

The official fixed-26 Aider Polyglot C++ suite and its prompts, tests,
references, overlays, candidate responses, and histories are held-out
evaluation evidence. They must not enter positive training data. Luna and
SynthMem artifacts may guide mechanism-level task quality only under their
declared provenance and feedback policies.

## Authorized CHARM V1 scope

The user-authorized Task Generation V1 scope is exactly:

- 17 frozen topics listed in
  `.agents/skills/charm-skill/references/task-generation-v1.md`;
- exactly three independently designed clean-room tasks per topic;
- exactly 51 planned tasks total;
- generation, executable proof, independent audit, owner remediation,
  private/final projection, and attempted pre-training corpus admission; and
- no model training, canary execution, checkpoint promotion, or deployment.

A topic addition, removal, rename, substitution, or count change requires a
reviewed protocol update before planning or reservation.

## Canonical workspace

Every new generation batch must first receive a permanent, atomically
reserved, exactly five-digit timestamp-derived batch code. The code is separate
from task IDs and is propagated through plans, tasks, receipts, projections,
and release lineage.

Use the CHARM workspace contract:

```text
dataset/
  tasks/{incoming,released,archived}/
  jsonls/{imported,staging,releases,manifests,hashes,release_notes}/
  temp/{generation_batches,merge_workspace,failed_tasks,repaired_tasks}/
  reports/{validation,improvement,scoreboards,history,release}/
  configs/
  scripts/
  docs/
  registry/
  dataset_manifest.json
  merge_queue.json
```

`dataset/tasks/` is canonical source. JSONL, reports, registries, hashes, and
manifests are generated projections or indexes. Repair owner-controlled
sources and regenerate downstream artifacts; never hand-edit generated tasks,
JSONL, reports, or receipts.

## Task-root privacy boundary

Public/model-facing material may contain only the unambiguous task contract,
starter state, editable files, and exact public API needed by a solver. Keep
solutions, private tests, hidden partitions, negative fixtures, oracle
receipts, expected outputs, and internal paths private.

Each admitted task requires exact API visibility, strict C++17/header
isolation, Weighted45 1.0, starter and two negative-control rejections,
determinism, portability, sanitizers, anti-cheat/nonce protection, protected
file integrity, and production application replay.

## Admission boundary

Task proof does not establish SFT-row readiness. Projection requires exact
tokenizer/template/mask/EOS replay, no truncation, no private leakage, and
final-state hash equality. Corpus admission additionally requires
repository-wide uniqueness, independent-audit closure, Baselines 1–3,
Validator V2 analysis, API reconstruction, curriculum/shape/exposure checks,
and a complete consumer dry-run.

Use separate statuses for task proof, audit, projection, dataset validation,
curriculum validation, training admission, corpus admission, consumer
verification, canary, promotion, and deployment. Missing evidence is
`not_completed`; no aggregate score overrides a hard failure.

## Successful local terminal claim

The strongest claim authorized by Task Generation V1 is:

```text
consumer_verified_sft_ready
```

That claim requires 51/51 selected tasks and cumulative V4.1 `pre-training`
PASS. Training, canary, promotion, and deployment remain unauthorized until a
later explicit request.
