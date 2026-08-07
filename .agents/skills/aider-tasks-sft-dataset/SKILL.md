---
name: aider-tasks-sft-dataset
description: Design, build, or verify deterministic Aider whole-edit private pre.jsonl and final train.jsonl projections from independently verified local generated task trees. Use when converting .w8-biayn/data/aider-tasks roots into canonical two-message SFT rows, comparing producer and final rows, excluding private controls, resolving task-ID lineage, or determining whether a projection is content-certified versus consumer-ready.
---

# Aider Tasks SFT Dataset

Project only independently verified, generator-owned tasks. Never write a
one-off converter, hand-edit generated task roots, or patch generated JSONL.

## Read first

Read completely:

1. `AGENTS.md`
2. `README.md`
3. `ROADMAP.md`
4. `docs/AIDER_SFT_SCOPE.md`
5. `.agents/skills/audit-sft-data-quality/SKILL.md`
6. `.agents/skills/audit-sft-data-quality/references/continuous-aider-sft-quality-loop.md`
7. `.agents/skills/audit-sft-data-quality/references/aider-fixed26-sft-improvement.md`
   when the data targets that capability distribution

Inspect the task owner, selected manifest, private receipts, requested output
root, and any existing projector implementation before changing projection
behavior.

## Availability gate

The approved narrow projector is `aider-task-validator project`, implemented
in `w8_biayn.aider_task_validator.projector`. It consumes only an exact
approved `charm-topic-manifest-v1` and digest-bound canonical task roots, then
writes private/final staged JSONL plus its manifest and hashes beneath a sibling
output directory. Use no shell converter, historical
`w8-biayn data aider-tasks-sft` command, or hand-authored JSONL.

This branch still has no release, tokenizer, loss-mask, split, export, or
consumer-verification pipeline. The projector can establish only
`producer_projection_verified`; later readiness remains `not_completed` unless
separately authorized and implemented.

## Required input gate

Accept only a frozen selected manifest whose exact tasks have:

- generator-owned current source and explicit new/replacement lineage;
- a clean fresh `$audit-sft-data-quality` report on the same tree hash;
- strict normal and fresh ASan/UBSan reference evidence;
- an executed plausible-but-wrong discriminator;
- task, test, reference, owner, compiler/image, and policy digest binding;
- benchmark-contamination and whole-corpus duplicate/family screens;
- zero retained `review`, conflict, or unresolved remediation findings.

Reject or quarantine stale receipts and same-ID competing revisions. Keep
selected, replaced, rejected, and review manifests separate.

## Authorized owner behavior

An approved projector must:

1. Consume only the selected manifest and current receipts.
2. Refuse `.state`, tests, CMake, private references, credentials, and private
   paths in model-facing content.
3. Write a private `aider-sft-pre-row-v1` `pre.jsonl` that binds exact public
   text, ordered starter/target files, safe final metadata, and private receipt
   digests.
4. Deterministically render exactly one `aider-sft-row-v1` final row for every
   pre row.
5. Preserve task ID, label, family/root identity, source revision, public text,
   file order, and file bytes.
6. Emit exactly two messages: user mask `0`, assistant mask `1`.
7. Emit only complete Aider whole-file listings in the assistant target.
8. Write beneath an ignored sibling output root without overwriting source,
   prior revisions, or immutable evidence.
9. Record source/pre/final hashes, renderer/policy identity, counts, and
   one-to-one mappings in a manifest.
10. Fail closed on missing files, duplicate IDs, conflicting lineage, stale
    evidence, sanitation that changes the contract, or output drift.

Legacy nine-message `aider-chat-v1` rows are migration input only. Remove the
system/demo/reset/acknowledgement transcript through the deterministic owner,
combine the actual starter and task into the user message, preserve the complete
C++ target, and regenerate. Never train on the legacy transcript merely because
it parses.

## Verify every projection

After the last source, receipt, manifest, renderer, pre-row, or final-row
change, run the complete validator:

```bash
uv run aider-task-validator validate path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --out path/to/train.validation \
  --baseline configs/aider_task_validator/aider-sft-row-v1-baseline.json
```

Validate every physical row and the complete corpus. Require authoritative
pre/final one-to-one and byte-exact comparison, no private leakage, strict row
schema, Markdown/file extraction, AST/API consistency, warning-free C++17
compile/link, sanitizer instrumentation compilation, duplicate/contamination
rules, and Progressive Baseline 3 for every retained row.

The serialized validator cannot run hidden semantic tests. Independently
confirm that each row's `verification_status` binds the current private normal,
runtime sanitizer, negative-fixture, and independent-audit receipt. Diagnostic
`--no-compile` or `--no-sanitizer-compile` runs cannot close the gate.

If `pre.jsonl` is unavailable, omit `--pre-jsonl`. The validator will emit an
advisory `pre_reconstruction.jsonl`; never release it or treat it as
authoritative provenance. This mode cannot claim
`producer_projection_verified`.

## Continuous repair

For every Baseline-3 failure:

1. Preserve `dataset_scores.csv`, `improvement_feedback.json`, and the exact
   report/dataset hashes.
2. Route source/task failures through `$aider-task-family-remediation`; route
   renderer-only failures through the projector owner.
3. Preserve stable identity and already-valid behavior; refresh revision,
   receipt, and hash metadata after content changes.
4. Regenerate complete affected roots, rerun private verification, obtain a
   fresh independent audit, and regenerate both JSONLs.
5. Validate the exact complete corpus again.
6. Repeat until every task passes Baseline 3 or record a concrete
   `not_completed` blocker.

Keep immutable controller snapshots per revision. Use the validator's
`revision_history.jsonl` and `best_revisions.json` as score/hash evidence, not
as task backups. Roll back only through the owner or an immutable controller
snapshot, then reverify.

## Handoff decision

Report separately:

- task-root status (`local_family_verified` or weaker);
- producer/final status (`producer_projection_verified` or weaker);
- serialized content status (`baseline3_content_certified` or weaker);
- consumer status (`consumer_verified_sft_ready` or `not_completed`).

Do not describe a local projection as a finalized release, tokenizer/mask
proof, training authorization, or benchmark-uplift result. The current branch
cannot establish `consumer_verified_sft_ready` without a separately authorized
consumer contract and implementation.

## Validate this skill

```bash
python3 .agents/skills/agent-skills-framework/scripts/validate_skill.py \
  .agents/skills/aider-tasks-sft-dataset
python3 /home/ubuntu/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/aider-tasks-sft-dataset
uv run pytest -q tests/test_aider_sft_scope_docs.py
```
