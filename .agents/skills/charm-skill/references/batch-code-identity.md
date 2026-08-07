# CHARM Five-Digit Batch-Code Identity

Use this contract for every new CHARM generation batch, including failed,
abandoned, replacement, recovery, retried, and concurrently planned batches.
The batch code is a separate identity alias. It does not replace or shorten the
immutable `generation_batch_id`, `generation_session_id`, or repository-global
task IDs.

## Format and derivation

Every batch has:

```text
generation_batch_created_at_utc = YYYY-MM-DDTHH:MM:SSZ
generation_batch_code = exactly five decimal digits, including leading zeroes
batch_code_derivation = unix-seconds-mod-100000-linear-probe-v1
```

Compute the initial code as the UTC Unix timestamp in whole seconds modulo
`100000`, formatted with five digits. A five-digit timestamp fragment is not
unique by itself. Under the canonical registry lock, if that code is already
claimed, probe `+1` modulo `100000` until the first free code is found. Record
the initial code and collision-probe distance. Fail closed if all 100,000 codes
are unavailable.

Uniqueness is repository-scoped and permanent. A rejected, abandoned,
released, superseded, or tombstoned batch keeps its code forever. Never derive
a code without atomically checking the complete registry, never recycle one,
and never describe the five-digit namespace as globally unique outside the
bound repository.

## Atomic reservation

`dataset/registry/batch_code_reservations.json` is the single append-only
authority for batch codes. Reserve the batch code before freezing proposal
packets or reserving task IDs:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_batch_code.py \
  --registry dataset/registry/batch_code_reservations.json \
  --batch-id <immutable-generation-batch-id> \
  --session-id <unique-generation-session-id> \
  --created-at <YYYY-MM-DDTHH:MM:SSZ> \
  --output <batch-code-reservation-receipt.json>
```

The utility holds the registry's canonical lock, writes atomically, and permits
only an exact same-batch, same-session, same-timestamp retry. A changed owner or
timestamp for an existing batch ID is a hard collision.

Bind the resulting code and receipt SHA-256 into the proposal plan, curriculum,
dependency manifest, task-ID reservation plan and receipt, task metadata,
task-proof receipts, independent-audit subject, private/final projection
metadata, release manifest, and final ledger. Every retained task in one batch
must carry the same code, and no retained task may claim a code owned by a
different batch.

## Historical assignment

Do not rewrite immutable historical task roots, JSONL, receipts, or release
artifacts merely to insert a batch code. Historical assignment is allowed only
as an append-only alias in the canonical batch-code registry when all of these
are known and digest-bound:

- the exact historical `generation_batch_id`;
- its original `generation_session_id`;
- an unambiguous UTC creation timestamp from immutable evidence; and
- the historical artifacts and status to which the alias applies.

The backfill receipt must say `historical_alias_only: true`. It supplements
lineage and does not repair, re-admit, release, or change the status of any old
task or batch. If the timestamp or batch boundary is ambiguous, report
`not_completed` instead of guessing.

