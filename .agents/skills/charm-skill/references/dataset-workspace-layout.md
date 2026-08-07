# Dataset Workspace Layout

Read this reference before Charm creates, moves, validates, merges, or releases
task/data artifacts.

## Authority

`tasks/` is the editable canonical source. `jsonls/`, reports, hashes,
registries, and manifests are deterministic projections or indexes. Repair the
owner-controlled task/generator source and regenerate downstream artifacts;
never patch generated JSONL or validation evidence.

## Root layout

```text
dataset/
├── tasks/{incoming,released,archived}/
├── jsonls/{imported,staging,releases,manifests,hashes,release_notes}/
├── temp/{generation_batches,merge_workspace,failed_tasks,repaired_tasks}/
├── reports/{validation,improvement,scoreboards,history,release}/
├── configs/
├── scripts/
├── docs/
├── registry/
├── dataset_manifest.json
└── merge_queue.json
```

Use `tasks/<state>/<topic>/vNNN/<task-id>/`, never flattened topic-version
names. One active authoring cycle covers one topic/version and targets 20 final
selected tasks by default. An explicit operator count is binding when the
curriculum, batch ledger, manifest, audit counts, and validation baseline all
record that same count. Rejected candidates remain traceable and replacements
retain lineage within the same topic/version.

## Per-task layout

```text
<task-id>/
├── pre.json
├── metadata.json
├── prompt.md
├── starter/
├── solution/
├── tests/
├── validator_cache/
└── revision_history/revision_NNNN.json
```

`metadata.json` records identity, topic/version, status, lineage, owner
revision, API/capability tags, and evidence digests. `pre.json` is a generated
task-level producer snapshot bound to the separated components. Treat
`validator_cache/` as disposable. Keep `solution/`, private tests, negative
fixtures, receipts, and staged `pre.jsonl` private.

## States and promotion

Use only:

```text
incoming -> validating -> repairing -> approved -> merged -> released
                                      \-> deprecated -> archived
```

Record every transition in metadata and task revision history. Promotion is an
atomic update of canonical path, task/topic registries, topic manifest,
dataset manifest, and merge queue. A folder move alone is not evidence.

## Topic manifest and registries

Each `tasks/<state>/<topic>/vNNN/manifest.json` records planned coverage cells,
the exact authorized selected-ID count (20 by default),
candidate/approved/rejected/replacement counts,
Baseline-3 count, V2 analysis status/profile/level/manifest hash when
projected, scores, validator decision, generator/compiler/audit/receipt
identities, policy/config hashes, and release membership. Derive every count
from reconciled artifacts.

Maintain object-indexed JSON registries for constant-time lookup:

- `task_registry.json`: path, status, topic/version, lineage, hashes, release;
- `topic_registry.json`: versions, coverage, counts, scores, certification;
- `api_registry.json`: APIs and C++ features for corpus balancing;
- `fingerprint_registry.json`: prompt/starter/target/AST/semantic fingerprints;
- `duplicate_index.json`: pairs, clusters, thresholds, dispositions;
- `batch_code_reservations.json`: append-only permanent five-digit batch-code
  claims, UTC timestamp derivation, collision probes, and owner sessions;
- `task_id_reservations.json`: append-only task-ID/slot claims, owner session,
  batch-code receipt, proposal binding, lifecycle state, and tombstones;
- `release_registry.json`: release membership, JSONLs, policy and hashes.

Never derive active membership from a filesystem scan when the registry exists.
Preserve archived entries and require exactly one active canonical version per
task ID.

Treat `registry/batch_code_reservations.json` as the single concurrency
authority for five-digit batch codes. Reserve a code before proposal freeze and
never recycle it, including after rejection, abandonment, or tombstoning.

Treat `registry/task_id_reservations.json` as the single concurrency authority
for every generation process sharing this dataset. Never create a per-session
copy. Acquire its canonical lock and atomically reserve all task IDs before
creating any task root. Every reservation binds `generation_batch_id`,
`generation_session_id`, topic, slot, proposal hash, and corpus-index hash.
Only an identical `reserved` claim may resume in the same session; all other
existing or tombstoned IDs are permanently unavailable. Registry/filesystem or
registry/manifest disagreement is a hard stop, not an invitation to overwrite
or silently repair state.

## JSONL, reporting, merge, and release

Keep imported legacy JSONLs under `jsonls/imported/` as unverified until their
canonical roots and current evidence exist. Generate private producer and final
candidate rows under `jsonls/staging/<run-id>/`. Promote only immutable,
versioned packages under `jsonls/releases/vNNN/`; never overwrite a release.

Store validator output under `reports/validation/<run-id>/` and retain every
run. Use the CSV and every per-task feedback object to drive owner repair. Once
all authorized topic rows pass Baseline 3 and the required non-certifying V2 batch
analysis is reconciled, enqueue the topic/version. Rebuild the whole dataset
from the task registry, deterministically merge/interleave it, and rerun both
V1 and the required V2 profiles on the complete corpus. Require full-corpus V2
Platinum before publishing release manifests, hashes, and notes.

## Configuration and scripts

Use strict versioned JSON accepted by the repository validator. Do not create
YAML because the current validator intentionally rejects it. Add generator,
compiler, duplicate, hallucination, reward, or consumer configs only when a
repository-owned command consumes and validates them. Add no one-off pipeline
script: every entrypoint needs defined inputs/outputs, idempotent transitions,
failure behavior, and tests.
