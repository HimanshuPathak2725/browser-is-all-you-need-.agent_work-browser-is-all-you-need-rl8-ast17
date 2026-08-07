# Repository-Wide Uniqueness Gate

Use this gate for every CHARM request that creates a new task. Run it after the
proposed problem contracts and coverage plan are frozen and before an owner,
generator, or materializer writes candidate task roots.

## Hard-pass rule

Generation is authorized only when every proposed problem is unique within the
proposed batch and has zero matches against every discoverable task artifact
under the repository root.

Treat all of the following as blocking outcomes:

- a reused or conflicting task ID;
- an exact raw or normalized prompt, contract, starter, target, reference,
  hidden-test oracle, or complete-row fingerprint;
- a materially equivalent observable contract, API behavior, solution
  strategy, meaningful edge-case set, or test oracle;
- a renamed, re-themed, constant-swapped, reordered, wrapper-only, or
  file-layout-only version of an existing problem;
- a near match that cannot be deterministically disproved;
- an unreadable or malformed candidate task artifact;
- an incomplete repository scan, stale index, missing comparison evidence, or
  missing receipt binding the frozen proposals and scanned corpus.

Stop before generation and report `not_completed` for any blocking outcome.
Do not downgrade it to a warning, sample the corpus, ignore a directory because
it is old or outside `updated task/`, or manually override a similarity result.

“Available” means the candidate task ID is absent from every task root, JSONL,
manifest, task/topic/release registry, historical or rejected ledger,
tombstone, and active reservation. If an ID is already registered, reserved,
materialized, verified, admitted, released, rejected, or tombstoned, do not
generate a new task under it. The only resumable case is an identical
`reserved` claim owned by the same generation session and proposal hash.

## Repository scope

Resolve the repository root from the checked-out worktree. Recursively discover
task-bearing artifacts across the entire root, including:

- canonical `tasks/incoming`, `tasks/released`, and `tasks/archived` roots;
- imported, staging, release, temporary, and historical task JSONL files;
- task roots and generated datasets outside `updated task/`;
- source inventories, selected/rejected/replaced manifests, task registries,
  duplicate indexes, and generation-batch ledgers;
- benchmark/task fixtures and other task collections present in the repository.

Exclude only version-control internals, dependency environments, opaque binary
objects, validator caches, and the new frozen proposal document being queried.
Record every exclusion explicitly. Do not exclude a location merely because it
contains an older copy, archived task, rejected task, temporary generation, or
different dataset version: it still proves the problem already exists.

If the repository contains linked worktrees or task roots outside the resolved
root that are named by manifests or registries, include their task inventories
or stop as `not_completed` when they cannot be read.

## Comparison procedure

1. Build a deterministic inventory of every discovered task record. Record its
   canonical path, container path and row when applicable, task ID, lineage,
   status, and content SHA-256.
2. Reconcile task-directory basenames with `metadata.json.task_id`, `pre.json`,
   topic manifests, `task_registry.json`, `dataset_manifest.json`, and active
   batch reservations. Stop on missing or conflicting identity evidence.
3. Create versioned fingerprints for each existing and proposed problem:
   raw bytes, normalized prompt/contract, starter files, API signature graph,
   target/reference code, structural AST/CFG, edge-case/test partition summary,
   hidden-test oracle, and a combined semantic-contract fingerprint.
4. Run exact-index lookups and all required near/semantic comparisons for every
   proposal against the complete inventory and against every other proposal.
   Use the repository-owned duplicate policy and its fixed thresholds. If no
   complete scanner exists, stop; do not substitute names or task IDs alone.
5. Treat any equality on a substantive fingerprint as a match. Treat a
   threshold match as blocking unless independent evidence proves that the
   observable behavior, solution strategy, edge cases, and oracle are all
   materially distinct.
6. Produce a zero-match receipt before reserving candidate IDs or writing task
   roots.
   Re-run the scan when any proposal, threshold, scanner version, registry,
   manifest, JSONL, task root, or repository task inventory changes.

## Required receipt

Persist a versioned, digest-bound pre-generation receipt containing:

- repository root and repository/worktree revision;
- scanner, normalization, parser, and duplicate-policy versions;
- scan start/end time, deterministic seed if any, included roots, explicit
  exclusions, files visited, task records parsed, and parse failures;
- frozen proposal-plan SHA-256 and one record per proposed problem;
- corpus/index SHA-256 and fingerprint schema version;
- within-batch and proposal-to-repository comparison counts;
- exact, near, structural, semantic, and ambiguous matches with paths and IDs;
- final `PASS` only when all match collections and parse-failure collections
  are empty;
- receipt SHA-256 and the owner/generator inputs it authorizes.

Bind the receipt hash into the coverage plan and generation readiness manifest.
The generator must verify that binding immediately before materialization.

## Atomic identity reservation after PASS

First follow `batch-code-identity.md`: atomically reserve one permanent,
exactly five-digit timestamp-derived batch code before proposal freeze. The
task-ID plan and receipt must bind that batch-code receipt, and a code owned by
another batch is a hard collision.

After the uniqueness receipt passes:

1. Assign one immutable `generation_batch_id`, its reserved five-digit
   `generation_batch_code`, one unique `generation_session_id` per invocation,
   and one immutable `(topic, slot_id)`
   for every planned task. For V1, each topic has exactly slots `1`, `2`, and
   `3`.
2. Build `charm-task-id-plan-v2` with `protocol_id`, batch code and its
   reservation-receipt SHA-256, candidate task ID, topic,
   slot, proposal SHA-256, frozen proposal-plan SHA-256, and uniqueness
   corpus-index SHA-256 for every claim. V1 uses
   `protocol_id=task-generation-v1`, exactly 51 claims across the exact frozen
   17-topic registry, and slots `1`, `2`, and `3` once per topic.
3. Require the zero-match receipt to prove reconciliation of the append-only
   reservation registry with the task, topic, release, manifest, rejected,
   archived, and tombstone indexes. A stale or disagreeing index is a hard
   failure; never auto-repair it inside generation. Then acquire the single
   canonical lock for `registry/task_id_reservations.json` and reread that
   registry while holding the lock.
4. Atomically compare and reserve the complete collision-free task-ID and slot
   set. A task ID is repository-global, not topic-local. A slot is unique within
   its batch. No check-then-write sequence outside the lock is valid evidence.
5. Permit an idempotent retry only when task ID, topic, slot, batch, owner
   session, proposal hash, and state are exactly the same and the state remains
   `reserved`. A different session or changed proposal must allocate a fresh
   ID and claim an unowned slot. It may never take over an existing claim.
6. Keep the lifecycle append-only:
   `proposed -> reserved -> materialized -> verified -> admitted/released` or
   `reserved/materialized/verified -> rejected_tombstone`. Never delete a claim
   and never reuse an admitted, released, rejected, abandoned, expired, or
   tombstoned ID. Stale reservations require explicit operator disposition;
   elapsed time alone does not transfer ownership.
7. Persist an atomic reservation receipt binding the registry before/after
   hashes, revision, lock acquisition, batch/session, plan, uniqueness receipt,
   corpus index, every task ID, every slot, and zero collisions. Bind this
   receipt into Generator Admission before materialization.
8. Pass the reserved IDs and receipt to the owner as structured input. The
   materializer must refuse unreserved IDs, foreign-session claims, terminal
   claims, existing destination roots, or an ID/slot/proposal mismatch. Create
   directories with exclusive semantics; never overwrite.
9. After generation and again before SFT admission, verify one-to-one identity
   propagation through directory basenames, metadata, task proofs, manifests,
   registries, projected rows, and the release ledger, then rerun the complete
   repository-wide comparison.

Use the bundled reservation utility after the uniqueness receipt and before
materialization:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_v1_task_ids.py \
  --registry dataset/registry/task_id_reservations.json \
  --plan path/to/task-id-plan.json \
  --uniqueness-receipt path/to/pre-generation-uniqueness.json \
  --batch-code-receipt path/to/batch-code-reservation-receipt.json \
  --output path/to/task-id-reservation-receipt.json
```

Every V1 session must use the same resolved canonical registry path. A
session-local copy is not a lock and cannot authorize generation. The
reservation utility serializes compliant sessions, rejects task-ID and slot
collisions, and allows only exact same-session retry. It does not replace the
repository-wide content uniqueness scan.

An explicitly authorized repair-in-place may reuse its existing canonical ID
and lineage because it is not a new problem. It still must not produce a second
retained root/row or match an unrelated task. A replacement or new task must
pass the complete pre-generation gate.
