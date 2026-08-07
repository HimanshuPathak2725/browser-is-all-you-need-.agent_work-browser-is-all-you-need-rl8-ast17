# GLM-4.7-Flash Aider Post-Training Roadmap

## Purpose

This worktree develops and evaluates GLM-4.7-Flash post-training for C++
repository editing. Miles provides training, Megatron-Core provides the
distributed backend, SGLang serves rollouts and evaluation, and the repository
owns the Aider C++ parsing, oracle, reward, dataset, and evidence contracts.

The immediate task-generation objective is the clean-room CHARM V1 batch. It
contains exactly 17 frozen topics, three independently designed tasks per
topic, and 51 tasks total. The official fixed-26 Aider Polyglot suite remains
held out and evaluation-only.

## Stage 0 — Freeze authority and evidence

Before task design:

- read `AGENTS.md`, `README.md`, this roadmap, `docs/AIDER_SFT_SCOPE.md`, and
  the complete CHARM skill;
- SHA-256 bind the active SynthMem post-run audit and Luna task-quality inputs;
- bind the exact operator-supplied `updated task/audit-sft-data-quality/` tree;
- reconcile evaluator health, all 311 attempt records, failure mechanisms, and
  the previous-best attempt ledger;
- freeze compiler, image, sanitizer, tokenizer, chat template, parser,
  feedback policy, and uniqueness-scanner bytes; and
- mark training, canary, promotion, and deployment unauthorized under the V1
  trigger.

Decision gate: `v1_scope_and_evidence_receipt.json` must hard-pass for the
exact 17 topics and 51 planned tasks.

## Stage 1 — Freeze the 51-task curriculum

Create the immutable iteration contract, family manifest, proposal packets,
and content-derived mixture required by Task Generation V1. Every topic has
slots 1, 2, and 3. Each task packet declares a novel story, exact public API,
starter/target topology, oracle delta, hidden partitions, mutations,
dependencies, and application budget before materialization.

Decision gate: failure-conditioned synthesis authorization must PASS with zero
invalid evidence, unresolved diagnosis, unauthorized disposition, missing
control, or contamination blocker.

## Stage 2 — Prove uniqueness and reserve identities

Before proposal freeze, atomically reserve one permanent exactly five-digit
timestamp-derived batch code under the canonical batch-code registry lock.

Run the complete repository-wide scanner across active, archived, imported,
staging, rejected, temporary, historical, fixture, and manifest-referenced
task artifacts. Exact, normalized, near, structural, API-graph, AST/CFG,
mutation, oracle, semantic, ambiguous, or parse-failure results all block.

After a zero-match receipt, atomically reserve all 51 repository-global task
IDs and `(batch, topic, slot)` claims in the one canonical append-only
`dataset/registry/task_id_reservations.json` under its lock.

Decision gate: permanent batch-code reservation, repository uniqueness,
atomic task-ID reservation, and Generator Admission V4.1 `pre-generation`
must all PASS and bind the same proposal.

## Stage 3 — Materialize and prove tasks

Generate through owner-controlled task-family sources under
`dataset/tasks/incoming/<topic>/vNNN/<task-id>/`. For each task require:

- exact public-API and isolated-header compilation;
- strict C++17 warnings-as-errors;
- target Weighted45 exactly 1.0;
- intended starter rejection;
- diagnosed-failure and distinct semantic mutation rejection;
- deterministic GCC/Clang, sanitizer, anti-cheat, nonce, and protected-file
  proof; and
- production whole-file parsing/application with exact final hashes.

Decision gate: all 51 per-task receipts, post-generation uniqueness, and
V4.1 `post-generation` PASS.

## Stage 4 — Independent audit and owner remediation

Run the independent dataset-quality auditor read-only on exact generated
bytes. Findings return to the owning generator, contract, starter, oracle, or
tests. Regenerate the complete affected family and rerun every invalidated
proof. Creator self-checks do not close independent findings.

Decision gate: a fresh independent receipt closes every finding for the exact
subject hashes.

## Stage 5 — Project and validate SFT rows

Project only digest-bound `local_family_verified` tasks to private
`pre.jsonl` and stripped final `train.jsonl`. Replay the production tokenizer,
chat template, token IDs, loss mask, EOS, context limit, whole-file parser, and
final applied state for every row. Private tests, targets, paths, receipts, and
expected outputs must not leak.

Decision gate: V1 Baseline 3, required Validator V2 analysis, V4.1 Baselines 1
and 2, API reconstruction, shape, exposure, consumer dry-run, and cumulative
`pre-training` admission all PASS.

## Stage 6 — Register truthful readiness

Only after cumulative admission, release immutable roots and register exact
task, JSONL, policy, toolchain, tokenizer/template, and receipt hashes. All 51
reservations receive one permanent final disposition.

Successful terminal state:

```text
topics = 17/17
tasks = 51/51
status = consumer_verified_sft_ready
training/canary/promotion/deployment = not authorized by the V1 trigger
```

Any partial result remains incomplete and must list its hard-failure IDs and
next owner action.

## Later stages requiring separate authority

A future explicit request may authorize the frozen 20-task, 5-epoch canary,
matched held-out evaluation, checkpoint promotion, or deployment
certification. Those stages retain the V4.1 stop conditions and cannot be
inferred from dataset readiness or low training loss.
