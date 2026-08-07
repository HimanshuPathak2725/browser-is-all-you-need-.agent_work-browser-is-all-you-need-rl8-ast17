# CHARM Task Generation V1

This is the canonical protocol for the exact trigger phrase
`Go for task generation V1`. Read it completely before taking any task action.

## Contents

- [Trigger contract](#trigger-contract)
- [Immutable V1 scope](#immutable-v1-scope)
- [Required evidence](#required-evidence)
- [Multi-session task-ID contract](#multi-session-task-id-contract)
- [Canonical agent prompt](#canonical-agent-prompt)
- [Exact ten-step workflow](#exact-ten-step-workflow)
- [Topic-specific task-quality guards](#topic-specific-task-quality-guards)
- [SFT-ready decision](#sft-ready-decision)

## Trigger contract

When the user says `Go for task generation V1`, invoke this protocol without
asking the user to restate it. Treat the phrase as authority to plan, generate,
validate, independently audit, repair through owner sources, project, and
attempt SFT corpus admission for Task Generation V1 only. It does not authorize
training, canary execution, checkpoint promotion, or deployment.

Run the ten steps below in order. Do not skip, merge, reorder, or self-certify a
step. A failed hard gate returns to its named owner-repair step. Never weaken a
threshold, edit a receipt, patch a generated task directly, or register a task
as SFT-ready to make the run finish.

## Immutable V1 scope

V1 requires exactly the following 17 topics and exactly three independently
designed tasks per topic: 51 tasks total. This is the complete, frozen V1
registry:

1. Allergies
2. Bank Account
3. Binary Search Tree
4. Circular Buffer
5. Clock
6. Complex Numbers
7. Crypto Square
8. Diamond
9. Grade School
10. Kindergarten Garden
11. Linked List
12. Parallel Letter Frequency
13. Phone Number
14. Spiral Matrix
15. Sublist
16. Yacht
17. Zebra Puzzle

The names, order, spelling, and count are immutable inside V1. Do not add an
eighteenth topic, substitute another benchmark family, omit a listed topic, or
label a non-51-task run as complete. Any scope change requires a reviewed skill
update and a new frozen registry hash.

For each topic, create exactly three tasks whose story, public API, starter
state, target action, code structure, oracle behavior, and mutation family are
independent. They may exercise the same broad capability, but they must not be
renamed, reworded, or type-substituted copies of Exercism, fixed-26, another V1
task, or any task anywhere in the repository.

## Required evidence

Read and bind these exact local artifacts before Step 1:

- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/DETAILED_POSTRUN_AUDIT.md`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/VALIDATOR_V4_SPEC.md`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/AUDIT_SUMMARY.json`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/failure-ledger/attempt_ledger.csv`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/failure-ledger/mechanism_summary.json`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/dataset_shape_audit.json`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/training_dynamics_audit.json`
- `artifacts/synthmem-v3-modal-eval4-20260803T054055Z/postrun-audit/receipt_consistency_audit.json`
- `artifacts/luna-cleanroom-evals/campaign-pass2-8x-20260801T100237Z/eight-run-metrics.json`
- `artifacts/luna-cleanroom-evals/campaign-pass2-8x-20260801T100237Z/task-frequency.json`

Use the Luna evidence only for task generation and task quality. Do not turn
provider revision, sampling nondeterminism, or an unsupported historical score
claim into task content.

## Multi-session task-ID contract

Every V1 invocation has one immutable `generation_batch_id`, one unique
`generation_session_id`, one exact UTC creation timestamp, and one permanent
exactly five-digit `generation_batch_code`. Derive and atomically reserve the
code through `batch-code-identity.md` before proposal freeze; the timestamp
fragment alone is not uniqueness proof. Every planned topic has exactly three
immutable slots,
`1`, `2`, and `3`. The task ID is repository-global; topic/version scoping does
not make a reused ID acceptable.

Before generation, search for each candidate ID in every task directory,
metadata/pre row, JSONL, manifest, registry, generation ledger, rejected or
archived record, tombstone, and active reservation. Then run the complete
content-uniqueness gate. After both are clear, atomically reserve the candidate
IDs and `(batch, topic, slot)` claims under the one canonical shared registry
lock. A session-local registry, unlocked existence check, filesystem-only scan,
or “last writer wins” update is a hard failure.

Use this lifecycle without deletion:

```text
proposed -> reserved -> materialized -> verified -> admitted/released
                         \-> rejected_tombstone
```

Only the same session may resume an identical `reserved` claim whose batch,
topic, slot, task ID, and proposal hash all match. If an ID is owned by another
session or is already materialized, verified, admitted, released, rejected,
abandoned, expired, or tombstoned, do not generate under it. Allocate a fresh
ID, rerun uniqueness on the changed plan, and obtain a new reservation receipt.
Never steal a stale claim automatically. This contract applies to sequential,
parallel, restarted, and retried V1 sessions.

## Canonical agent prompt

Use the following prompt as the governing instruction when the V1 trigger is
received:

> You are the CHARM Task Generation V1 owner. Execute the local
> `charm-skill` point by point. Generate exactly three high-quality,
> clean-room Aider C++ SFT tasks for each of the frozen 17 topics, for exactly
> 51 tasks total. Do not begin materialization unless the topic registry
> exactly matches all 17 frozen names, the failure-conditioned synthesis
> authorization passes, the repository-wide pre-generation uniqueness receipt
> passes, and Generator
> Admission V4.1 `pre-generation` passes.
>
> Every task must be a genuinely new problem. Search the entire repository and
> every active, archived, imported, rejected, staging, fixture, temporary,
> linked-worktree, manifest-referenced, and generated task location before and
> after generation. Reject exact, normalized, near, structural, API-graph,
> AST/CFG, mutation, test, oracle-behavior, or semantic matches. Ambiguity,
> incomplete scan scope, or parse failure is FAIL.
>
> Give this invocation an immutable generation batch ID and unique session ID.
Before proposal freeze, atomically reserve its permanent exactly five-digit,
timestamp-derived batch code in the canonical batch-code registry. Propagate
that code and receipt digest through every plan, task, receipt, projection, and
ledger; never recycle a rejected or tombstoned batch code.
> For every topic, bind slots 1, 2, and 3 to candidate task IDs. Check every ID
> against all task roots, JSONLs, manifests, permanent registries, rejected and
> archived ledgers, tombstones, and active reservations. After the complete
> uniqueness scan passes, acquire the one canonical shared registry lock and
> atomically reserve all IDs and slots before creating a task directory. If an
> ID already exists or belongs to another session, do not generate under it;
> choose a fresh ID and repeat uniqueness. Resume only the same session's exact
> still-reserved claim. Never overwrite, steal, delete, or reuse a terminal or
> tombstoned ID.
>
> Do not rely on the model remembering a historical Exercism API. Put the exact
> case-sensitive namespace, class/free-function names, signatures, types,
> qualifiers, templates, exceptions, editable files, and output contract in the
> public prompt or starter. Derive an API manifest before code. If the starter
> header lacks or misdeclares a required symbol, make the header editable and
> require the target to change it. A nonempty starter never implies a protected
> header or source-only answer.
>
> Run the exact ten-step workflow. For every failure, preserve evidence, repair
> the owner-controlled generator, contract, starter, oracle, or tests,
> regenerate the complete affected task/family, invalidate downstream receipts,
> and restart at the earliest invalidated step. Never patch generated roots,
> JSONL, reports, or PASS receipts directly.
>
> Register a task or corpus as SFT-ready only after per-task proof, independent
> audit closure, exact projection and serialization replay, repository-wide
> post-generation uniqueness, V1 Baseline 3, required Validator V2 analysis,
> strengthened V4.1 Baselines 1 and 2, API predictor, dataset-shape and
> curriculum admission, consumer dry-run, and cumulative V4.1
> `pre-training` PASS all bind the same immutable subject hashes. Otherwise
> report `not_completed` or `failed` with hard-failure IDs and do not
> register it.
>
> Treat the prior failures as mandatory negative design constraints: prevent
> missing or misnamed public APIs, wrong case or namespace, header/source action
> mistakes, missing direct standard-library includes, private-member misuse,
> mixed integer type compile errors, warning-as-error failures, member
> shadowing, pointer update-order corruption, reserve-versus-resize lifetime
> errors, response truncation, unapplied whole-file edits, and feedback leakage.
>
> Preflight the build environment across all 51 tasks, not a sample. Every
> declared dependency must be present and hash-bound. Prefer the standard
> library. An unsupported external dependency or CMake configuration failure is
> an infrastructure/task-package failure and blocks admission; it must never be
> counted as a model semantic failure.
>
> Keep prompts deterministic and hash-bound. Identical task inputs must render
> byte-identical first-request prompts under the frozen serializer. Keep
> Pass@1, cumulative feedback@2, repair-on-attempt-2, and sample-union metrics
> distinct. Use the same declared, sanitized feedback policy in repair rows and
> evaluation: at most 100 lines, actionable public compiler diagnostics
> allowed, but no private test names, paths, assertions, hidden expected values,
> or hidden case structure.
>
> Finish only with an immutable ledger listing all 51 planned tasks, generated,
> rejected, repaired, selected, and SFT-ready counts; every receipt hash; every
> unresolved blocker; and the exact next authorized action. A score, judge
> opinion, low loss, or partial baseline cannot override a hard failure.

## Exact ten-step workflow

### Step 1 — Resolve scope, authority, evidence, and dependencies

1. Read `SKILL.md` and every reference it routes to for generation,
   uniqueness, workspace layout, failure conditioning, V4.1, and Validator V2.
2. Hash-bind every required audit artifact and the operator-supplied updated
   audit-skill tree.
3. Verify the V1 topic registry exactly matches the 17 frozen names above,
   without additions, omissions, substitutions, duplicates, or placeholders.
4. Compute `17 * 3 = 51`; reject any other planned count.
5. Assign and freeze one `generation_batch_id`, one unique
   `generation_session_id`, and an exact UTC creation timestamp. Atomically
   reserve its permanent exactly five-digit `generation_batch_code` under the
   canonical batch-code registry lock, then freeze both canonical registry paths.
6. Reconcile that registry with every permanent task/topic/release registry,
   manifest, task root, JSONL, historical/rejected ledger, tombstone, and active
   reservation. Stop on stale, missing, unreadable, or disagreeing identity
   evidence.
7. Resolve generation/projection authority only. Mark training, canary,
   promotion, and deployment unauthorized.
8. Freeze compiler, C++ standard, build image, sanitizer availability, complete
   dependency manifest, tokenizer, chat template, whole-file parser, feedback
   policy, and uniqueness scanner bytes.
9. Configure and compile a dependency/preflight probe for every planned task
   package; do not sample only the first tasks.

Hard PASS output: `v1_scope_and_evidence_receipt.json`. Any topic-name, topic-
count, or planned-task-count mismatch stops here with
`not_completed: v1_topic_registry_mismatch`.

### Step 2 — Freeze the 51-task curriculum and generation contract

Create the exact task manifest before materialization. Use these integer counts
for 51 tasks:

| Dimension | Frozen V1 count |
| --- | ---: |
| Direct verified success | 27 |
| Boundary case | 10 |
| Genuine repair trajectory | 11 |
| Calibration/no-change | 3 |
| Empty starter | 10 |
| Skeleton starter | 13 |
| Partial implementation | 10 |
| Semantic-bug starter | 8 |
| Compile-bug starter | 5 |
| Near-correct starter | 5 |
| CPP-only editable layout | 17 |
| Header-only editable layout | 8 |
| Header+CPP editable layout | 26 |
| More than two editable files | at least 6, overlapping layout counts |
| Frozen header mode | 11 |
| Editable header mode | 10 |
| Reconstructed header mode | 10 |
| Repaired header mode | 10 |
| Extended header mode | 10 |

Require at least 15 content-proved tasks for each API capability:
implement-missing, preserve, extend, repair, and refactor. Require every repair
subtype—compile, linker, API, hidden-test, runtime, and sanitizer—in at least one
of the 11 repair trajectories; overlap requires proof. Require at least one
independently verified non-synthetic direct-success source; if none is
available, fail admission instead of relabeling a generated row.

Freeze—but do not execute under this trigger—the downstream V4.1 canary plan:
exactly 20 tasks, 5 epochs, four frozen matched trials, evaluation at every
checkpoint, early stopping, and the 40/40/20 selection policy.

For each topic, predeclare three distinct task packets. Each packet binds:

- repository-global candidate task ID and immutable slot `1`, `2`, or `3`;
- independent story and behavioral contract;
- exact case-sensitive public API manifest;
- starter and target file hashes;
- editable/protected files and required target action;
- role, starter type, header mode, API capability, difficulty, and failure class;
- oracle delta, hidden partitions, negative mutations, and sanitizer policy;
- expected build dependencies and portability policy; and
- response/application budget.

Hard PASS outputs: iteration contract, generation plan, family manifest, and
failure-conditioned synthesis-authorization receipt.

### Step 3 — Hard-pass repository-wide uniqueness before generation

Run the CHARM repository-wide uniqueness gate against the entire accessible
directory scope. Compare topic proposals, contracts, identifiers, API graphs,
starter structures, target design sketches, tests, mutations, oracles, and
semantic behavior.

Any task-ID occurrence, existing/tombstoned/reserved identity, content match,
near match, ambiguous review, incomplete scope, linked-worktree omission, or
parse failure blocks generation. Bind the exact generation-plan SHA-256 into
the uniqueness receipt.

After uniqueness PASS, build `charm-task-id-plan-v2` with all 51 task IDs,
`protocol_id=task-generation-v1`, topics, slots, proposal hashes, the
proposal-plan hash, corpus-index hash, `generation_batch_id`,
`generation_session_id`, `generation_batch_created_at_utc`,
`generation_batch_code`, and the batch-code receipt SHA-256. Atomically reserve
the complete set through the canonical shared registry:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_v1_task_ids.py \
  --registry <dataset-root>/registry/task_id_reservations.json \
  --plan <v1-task-id-plan.json> \
  --uniqueness-receipt <v1-pre-generation-uniqueness.json> \
  --batch-code-receipt <v1-batch-code-reservation-receipt.json> \
  --output <v1-task-id-reservation-receipt.json>
```

The reservation receipt must prove one owner-bound claim per planned task,
three unique slots per topic, zero collisions, lock acquisition, and registry
before/after hashes. A different-session collision or an existing destination
requires fresh IDs and a restart of Step 3. An exact same-session retry may
resume its unchanged `reserved` claims without creating duplicates.

Then run:

```bash
python3 .agents/skills/charm-skill/scripts/validate_generation_readiness.py \
  --stage pre-generation \
  --input <v1-admission-bundle.json> \
  --output <v1-pre-generation-receipt.json>
```

Bind the reservation plan and receipt into the admission bundle. Do not
materialize until uniqueness, atomic reservation, and V4.1 all return PASS.

### Step 4 — Generate three independent tasks per topic

Generate one topic and version at a time through the owner-controlled task
generator under `tasks/incoming/<topic>/vNNN/<task-id>/`.

Immediately before each write, verify that the current session still owns the
exact batch code, reserved task ID, topic, slot, and proposal. Create each task directory
exclusively and fail if it already exists. Never replace another session's
directory or regenerate a task whose reservation is already terminal.

For each topic, ensure the three tasks differ in at least:

- public API graph;
- starter shape;
- target file-action topology;
- principal invariant/failure mechanism;
- oracle behavior and hidden-test partitions; and
- reference implementation AST/CFG or solution strategy.

Do not copy benchmark text, historical API, tests, identifiers, examples,
reference code, or hidden behavior. Broad topic inspiration is allowed only
when the resulting task is independently specified and passes all six
uniqueness levels.

Make the public prompt sufficient to implement the exact API without historical
memory. Keep hidden tests hidden, but never hide the public interface or public
behavior needed for a valid implementation.

### Step 5 — Execute the per-task proof loop

For each exact task, build an isolated temporary workspace and require:

1. exact public-API compile probe;
2. isolated-header strict warnings-as-errors build;
3. reference/oracle Weighted45 exactly `1.000000`;
4. starter rejection for the declared reason;
5. diagnosed failure mutation rejection;
6. distinct compiling semantic mutation rejection;
7. GCC/Clang and deterministic grader proof;
8. ASan/UBSan and applicable TSan proof;
9. anti-cheat, dynamic nonce, protected-file, and companion-file proof; and
10. production whole-file parse/application replay with exact final hashes.

Also prove all hidden partitions are reachable, independent enough to add
signal, deterministic, and free from timing, locale, random, filesystem,
pointer-layout, or unsupported-dependency assumptions.

On failure, record observed/expected/evidence/reason/remediation, repair the
owner source, regenerate, and rerun all ten checks. No task proceeds on partial
credit.

### Step 6 — Post-generation uniqueness and independent audit loop

Rerun repository-wide uniqueness against exact generated bytes and all
directories. Reconcile every generated task ID and slot with its reservation,
directory basename, metadata, proofs, manifests, and task registry. A missing,
foreign, duplicated, or terminal-state mismatch fails. Then run V4.1
`post-generation`.

Invoke the independent dataset-quality auditor read-only. It must receive raw
artifacts, not the desired verdict. For every finding:

```text
independent finding
  -> owner diagnosis
  -> owner-source repair
  -> regenerate complete affected task/family
  -> invalidate downstream receipts
  -> rerun Step 5
  -> rerun post-generation uniqueness
  -> fresh independent audit
```

Close findings only with a new independent receipt. Creator self-checks cannot
close the audit.

### Step 7 — Project exact private and final SFT data

Project only immutable, digest-bound `local_family_verified` roots through the
approved projector. Produce private `pre.jsonl` and stripped final
`train.jsonl`.

For every row, replay the production tokenizer and chat template and prove:

- exact rendered prompt and token IDs;
- exact loss mask and EOS placement;
- no truncation;
- correct whole-file parsing and file application;
- editable/protected scope;
- final applied target hash;
- no private tests, targets, receipts, expected outputs, or paths leaked; and
- genuine four-turn repair structure where assigned.

Require byte-identical prompt serialization from identical inputs. A prompt hash
drift without an authorized input change fails.

### Step 8 — Run dataset, curriculum, baseline, and consumer validation

Recompute all content-derived roles, starters, layouts, header modes, API
capabilities, repair subtypes, families, origins, difficulty, AST/API shapes,
and exposure counts from exact selected rows.

Require:

- one selected row per admitted task and exact receipt reconciliation;
- zero duplicate, heldout, ancestor/descendant, ambiguous, or unresolved cases;
- V1 Baseline 3 PASS on the complete private/final pair;
- count-matched Validator V2 topic analysis and required full-corpus claim;
- V4.1 Baseline 1 at least 90;
- V4.1 Baseline 2 at least 95;
- 100% critical, at least 98% major, and at least 95% minor rules;
- deterministic API reconstruction score at least 97% and predicted risk at
  most 3%;
- complete dataset-shape histograms with no family below its minimum;
- repair coverage at least 20%, calibration at least 5%, duplicate risk below
  2%, and generalization risk at most 0.30;
- exact planned exposure and zero curriculum drift; and
- a consumer dry-run that loads every row without schema, mask, tokenizer,
  parser, or path failure.

Any failure returns to the owning earlier step. Do not hand-edit projected
JSONL.

### Step 9 — Cumulative pre-training admission

Assemble all exact task, uniqueness, audit, projection, serialization, corpus,
baseline, predictor, shape, exposure, and consumer receipts under one immutable
subject manifest.

Run V4.1 `pre-training`. Independently recompute the hard-failure list and
assert all receipt subject hashes agree. The decision is conjunctive; an
aggregate score cannot mask a failed task or baseline.

A PASS authorizes only the dataset status
`consumer_verified_sft_ready` and the separately controlled bounded canary.
It does not authorize a full training run.

### Step 10 — Register SFT-ready truthfully

Only after Step 9 PASS:

1. move immutable task roots through the repository release workflow;
2. register exactly the admitted task IDs and versions;
3. register the permanent five-digit batch code and final `train.jsonl`,
   manifest, tokenizer/template, policy, compiler/image, and receipt hashes;
4. set `task_status=local_family_verified`;
5. set `projection_status=producer_projection_verified`;
6. set `corpus_admission_status=pretraining_v4_1_admitted`;
7. set `consumer_status=consumer_verified_sft_ready`; and
8. leave canary, training, promotion, and deployment statuses pending.

Atomically transition each selected reservation to `admitted/released` and
each rejected or abandoned reservation to `rejected_tombstone`. Preserve both
forever; neither class may be deleted or reused by a later V1 session. Verify
that all 51 planned slots have exactly one final disposition and no active
foreign-session owner.

Write a final ledger with planned 51, generated, regenerated, rejected,
selected, and SFT-ready counts. If selected is not exactly 51, do not present
the V1 batch as complete. Report every blocker and next owner action.

## Topic-specific task-quality guards

These are negative design constraints, not permission to reproduce benchmark
APIs or tests.

| Topic | Prior task-quality signal | Required V1 safeguards across its three novel tasks |
| --- | --- | --- |
| Allergies | Required API often absent or misnamed | Explicit bitmask/domain API; case-sensitive probe; zero/unknown-bit boundaries; at least one existing-header edit |
| Bank Account | State API such as open/close was omitted; repair improved more than first-turn | Explicit lifecycle API and invalid transitions; thread-safety where declared; linker/API repair trajectory |
| Binary Search Tree | Required tree type was invisible | Explicit templated/non-templated choice, ownership and duplicate policy; header placement proof; traversal invariants |
| Circular Buffer | Missing API and reserve-versus-resize segfault | Constructed-element lifetime, overwrite/full/empty rules, nontrivial element tests, ASan/UBSan and exception safety |
| Clock | Wrong case/type API was generated | Exact case-sensitive namespace/type/factory/operators; wraparound and negative normalization; no historical-name guessing |
| Complex Numbers | Candidate accessed private representation | Public accessor/operator contract, encapsulation-safe implementation, precision rules, strict compile probe |
| Crypto Square | Class-versus-free-function mismatch, unused parameter under `-Werror`, malformed outputs | Explicit object/function topology, full use of inputs, formatting/termination budget, warning-clean build |
| Diamond | API mismatch plus semantic symmetry failure | Exact return type and symbol, width/symmetry invariants, boundary characters, deterministic whitespace oracle |
| Grade School | Public header omitted direct `<set>` include | Self-contained headers, direct includes, ordering/duplicate invariants, include-removal negative mutation |
| Kindergarten Garden | Missing enum/API and missing `<algorithm>`/`<stdexcept>` | Explicit domain types and mapping order, direct includes, invalid-input contract, no ambient transitive includes |
| Linked List | Missing type; link destroyed before it was read | Ownership model, empty/singleton/multi-node invariants, read-before-unlink ordering, sanitizer and compiling mutation |
| Parallel Letter Frequency | Missing `unordered_map`; incompatible `std::min` types | Direct includes, explicit key/count types, zero-worker policy, partition/join correctness, race and type-conversion probes |
| Phone Number | Local variable shadowed member state | Constructor-to-member state transfer, invalid-input representation, normalization boundaries, shadowing mutation |
| Spiral Matrix | Repeated API absence; some Luna outputs malformed despite semantic successes | Explicit dimensions/return shape, zero/one/rectangular boundaries as declared, output-size budget and applied-file proof |
| Sublist | Exact relation API was frequently guessed incorrectly | Explicit relation type and names, generic/value constraints, empty/equal/repeated-pattern cases, complexity bound |
| Yacht | Category representation was guessed as enum instead of required string in historical eval; headers also failed | Declare category representation explicitly, reject unknown categories, exhaustive scoring boundaries, direct includes |
| Zebra Puzzle | `solve` declaration/definition omitted; long output left starter-like files | Explicit result type and solve entry point, deterministic constraints, bounded solution strategy, completion/application proof |

Across all topics, prohibit task-name clones and identical API/test/oracle
deltas. At least two action topologies and one existing scaffold are required
within every topic family.

## SFT-ready decision

The only successful terminal statement for this protocol is:

```text
Task Generation V1:
topics = 17/17
tasks = 51/51
per-task proof = PASS
repository uniqueness = PASS before and after generation
batch-code reservation = PASS, five-digit, permanent, and fully reconciled
task-ID reservations = PASS, owner-bound, and fully reconciled
independent audit = closed by fresh receipt
projection and serialization = PASS
V1 Baseline 3 = PASS
Validator V2 required claim = PASS
V4.1 Baseline 1 = PASS
V4.1 Baseline 2 = PASS
V4.1 pre-training admission = PASS
consumer dry-run = PASS
status = consumer_verified_sft_ready
training/canary/promotion/deployment = not authorized by this trigger
```

Any other result is incomplete or failed. Preserve partial evidence, but never
use the label SFT-ready.
