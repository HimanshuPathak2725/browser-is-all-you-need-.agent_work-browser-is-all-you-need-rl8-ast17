---
name: charm-skill
description: Create, validate, independently audit, repair, project, canary-test, promote, and deployment-certify clean-room Aider C++ SFT tasks with repository-wide uniqueness, atomic multi-session task-ID reservation, failure-conditioned synthesis authorization, public-API/action-topology remediation, executable oracle proof, curriculum and training admission, checkpoint dynamics, Baseline-3, Validator V2, and cumulative Generator Admission V4.1 gates. Use whenever the user says "Go for task generation V1" to execute the frozen V1 topic protocol and exact 10-step generate-validate-admit loop, and for CHARM task generation, concurrent or repeated generation sessions, one-topic batches, task roots, manifests and registries, private pre.jsonl/final train.jsonl, corpus or training admission, canary, checkpoint promotion, deployment certification, or a final manual generation-readiness review.
---

# CHARM Skill

Produce evidence-authorized, globally unique, executable Aider C++ task roots
and verified SFT projections. Keep generation, independent audit, projection,
serialized validation, canary evaluation, and promotion separate. Never let one
stage self-certify the next.

## Read first

Read these sources completely before the corresponding stage:

1. Repository `AGENTS.md`, `README.md`, `ROADMAP.md`,
   `docs/AIDER_SFT_SCOPE.md`, and validator documentation.
2. `.agents/skills/aider-sft-task-creator/SKILL.md` before task design.
3. `.agents/skills/aider-task-family-remediation/SKILL.md` before repair.
4. `.agents/skills/audit-sft-data-quality/SKILL.md` before independent audit.
5. `.agents/skills/aider-tasks-sft-dataset/SKILL.md` before projection.
6. The exact operator-supplied `updated task/audit-sft-data-quality/` folder
   before any new synthesis.
7. [task-generation-v1.md](references/task-generation-v1.md) completely when
   the user says `Go for task generation V1`; execute its ten steps exactly.
8. [dataset-workspace-layout.md](references/dataset-workspace-layout.md) before
   creating, moving, merging, or releasing artifacts.
9. [batch-code-identity.md](references/batch-code-identity.md) before naming,
   planning, retrying, recovering, or backfilling any generation batch.
10. [repository-wide-uniqueness-gate.md](references/repository-wide-uniqueness-gate.md)
    before planning task IDs or materializing tasks.
11. [failure-conditioned-generation-gate.md](references/failure-conditioned-generation-gate.md)
    before designing a task.
12. [generator-admission-v4.md](references/generator-admission-v4.md) before
    generation, after materialization, before training, and before promotion.
13. [training-admission-promotion-v4-1.md](references/training-admission-promotion-v4-1.md)
    before freezing curriculum, admitting training, running a canary, promoting
    a checkpoint, or certifying deployment.
14. [validator-v2-gate.md](references/validator-v2-gate.md) before projecting,
    merging, certifying, or releasing JSONL.

Use instructions and commands from the active checked-out branch. A document
or receipt from another branch is evidence only when its exact bytes and
revision are explicitly bound.

## Active non-optional remediation profile

Until matched promotion evidence closes it, every generation request must bind
the post-run profile `synthmem-v3-modal-eval4-20260803T054055Z`:

- 311 attempts, 288 failures;
- 281 compile/link failures;
- 264 public-API-visible failures;
- zero existing-header training edits;
- zero genuine repair trajectories;
- zero calibration rows;
- silently halved successful-anchor exposure;
- near-zero training loss with zero training-time evaluation; and
- recorded mean Pass@1 regression from 9/26 to 1/26.

This profile makes public API completeness, correct file-action selection,
genuine redacted-feedback repair, anchor retention, and bounded canary testing
hard gates. Do not generate “more hard examples” without this exact causal
contract.

## Task Generation V1 exact trigger

When the user says `Go for task generation V1`, immediately load the complete
V1 reference and execute its ten numbered steps. Do not ask the user to paste
the prompt again and do not substitute a generic CHARM workflow.

The phrase authorizes generation, validation, owner remediation, projection,
and attempted SFT admission for V1 only. It does not authorize training,
canary, promotion, or deployment. The current V1 registry is frozen to exactly
the 17 operator-supplied topics in the V1 reference, with exactly three tasks
per topic and 51 tasks total. A topic addition, removal, rename, substitution,
or different task count requires a reviewed skill update. Never infer an
eighteenth topic or execute V1 against an alternative topic list.

## Resolve authority and status

Determine whether the user authorized task roots, JSONL projection, a bounded
canary, full training, evaluation, export, or promotion. Earlier-stage authority
does not imply later-stage authority.

Use separate statuses:

```text
failure_evidence_status
generation_admission_status
task_proof_status
independent_audit_status
projection_status
dataset_validation_status
curriculum_validation_status
training_admission_status
corpus_admission_status
canary_status
training_dynamics_status
consumer_status
promotion_status
deployment_certification_status
```

Unavailable prerequisites are `not_completed`. Scores, model-judge approval,
operator preference, low loss, or an earlier-stage PASS cannot override a hard
failure.

## Enforce the workspace contract

Treat `tasks/` as canonical source and `jsonls/` as generated output. Follow
the workspace reference.

- Author one topic/version at a time and freeze the exact operator count.
- Create only under `tasks/incoming/<topic>/vNNN/<task-id>/`.
- Promote immutable roots to `tasks/released/`; archive replaced roots with
  lineage.
- Keep private targets, tests, negative fixtures, receipts, and `pre.jsonl`
  outside model-facing and release payloads.
- Reconcile task/topic/API/fingerprint/duplicate/release registries, manifests,
  and merge queues at every transition.
- Use one canonical append-only `batch_code_reservations.json`. Before
  proposal freeze, atomically reserve one permanent, exactly five-digit
  timestamp-derived `generation_batch_code` for the immutable batch/session.
  Never recycle a code; resolve modulo collisions under the registry lock.
- Use one canonical append-only `task_id_reservations.json` for all generation
  sessions. A per-session registry copy is invalid.
- Under its canonical lock, atomically reserve every repository-global task ID
  and batch/topic slot before materialization. An existence check followed by
  an unlocked write is not a PASS.
- Resume only an identical `reserved` claim owned by the same batch, session,
  slot, and proposal. Never reuse or take over an admitted, released, rejected,
  abandoned, expired, foreign-session, or tombstoned ID.
- Never overwrite reports or released data.
- Repair owner-controlled generators/contracts/tests, then regenerate. Never
  patch generated roots, JSONL, reports, or receipts directly.

## Execute the cumulative pipeline

Run the detailed state machine in the V4 reference. The governing sequence is:

```text
freeze valid evaluation evidence and previous-best attempt ledger
  -> diagnose mechanisms and authorize synthesis
  -> atomically reserve the permanent five-digit timestamp-derived batch code
  -> freeze iteration, mixture, action, feedback, exposure, and canary plans
  -> HARD PASS repository-wide uniqueness before generation
  -> HARD PASS Generator Admission V4.1: pre-generation
  -> atomically reserve IDs/slots in the shared registry under lock
  -> verify the reservation receipt in Generator Admission
  -> materialize exclusively through the owning session and generator
  -> prove every task with API/oracle/grader/safety/application receipts
  -> HARD PASS repository-wide uniqueness after generation
  -> HARD PASS Generator Admission V4.1: post-generation
  -> independent read-only audit and owner remediation loop
  -> project private pre.jsonl and final train.jsonl
  -> exact tokenizer/template/mask/EOS/application replay
  -> HARD PASS dataset and curriculum validation
  -> HARD PASS strengthened Baselines 1-3 and required V2 topic analysis
  -> HARD PASS API predictor, shape, drift, exposure, and training admission
  -> HARD PASS Generator Admission V4.1: pre-training
  -> run exactly the frozen 20-task, 5-epoch canary
  -> log train/validation loss, compile, and hidden-test rate every checkpoint
  -> early-stop and select the best 40/40/20 composite checkpoint
  -> matched held-out and unseen shadow evaluation
  -> HARD PASS Generator Admission V4.1: promotion
  -> consumer, artifact, rollback, monitoring, security, and reproducibility proof
  -> HARD PASS Generator Admission V4.1: deployment
  -> only then authorize the declared deployment transition
```

Any prompt, starter, target, reference, test, negative fixture, generator,
renderer, selected manifest, compiler/image, tokenizer/template, feedback
policy, uniqueness index, or verification-policy change invalidates downstream
receipts.

## Hard pass before generation

Generation is forbidden until both independent receipts pass and bind the same
proposal plan:

1. failure-conditioned synthesis-authorization receipt; and
2. Generator Admission V4.1 `pre-generation` receipt.

At minimum require:

- exact updated-task audit-skill tree and active failure artifacts by SHA-256;
- healthy evaluator, zero unresolved diagnoses, and authorized dispositions;
- previous-best attempt-ledger hash;
- repository-wide uniqueness with zero exact, near, structural, semantic,
  ambiguous, or parse-failure records;
- exactly one candidate ID and slot claim per planned task, absent from every
  repository task root, registry, manifest, JSONL, ledger, tombstone, and active
  reservation;
- atomic permanent five-digit batch-code reservation owned by the current
  generation session, with timestamp derivation, collision probe, and registry
  before/after hashes;
- atomic zero-collision ID reservation owned by the current generation session,
  bound to the batch-code receipt, proposal plan, uniqueness receipt, corpus
  index, and registry before/after hashes;
- content-derived role ranges: direct 50-70%, boundary 15-25%, genuine repair
  20-30%, calibration 5-8%;
- editable layouts: CPP-only <=40%, header-only 10-20%, header+CPP >=40%,
  and more-than-two-file tasks >=10%;
- starter targets 20/25/20/15/10/10 for empty, skeleton, partial,
  semantic-bug, compile-bug, and near-correct, each within five points;
- at least 15 tasks each for implement/preserve/extend/repair/refactor API;
- at least 5% of repair rows for every required repair subtype;
- frozen/editable/reconstructed/repaired/extended header modes each 10-30%;
- complete dataset-shape histograms with no family below its frozen minimum;
- at least two action topologies and one existing scaffold per family;
- at least one verified non-synthetic source;
- redacted feedback identical between repair training and promotion, at most
  100 lines, with no hidden answers, expected outputs, or private test names;
- exact builder, verifier, eval wrapper, policy, tokenizer, template, heldout,
  and uniqueness-scanner source bytes;
- exact planned anchor exposure with zero silent drift;
- deterministic API reconstruction score >=97% and predicted failure <=3%;
- per-checkpoint dynamics plus early stopping and 40/40/20 selection; and
- a frozen 20-task, 5-epoch canary with full training blocked until PASS.

Use the bundled template and validator:

```bash
cp .agents/skills/charm-skill/assets/charm-generator-admission-v4.template.json \
  path/to/charm-generator-admission-v4.json

python3 .agents/skills/charm-skill/scripts/validate_generation_readiness.py \
  --stage pre-generation \
  --input path/to/charm-generator-admission-v4.json \
  --output path/to/pre-generation-receipt.json
```

The template deliberately fails until all placeholders are replaced and
`example_only` is set to `false`.

Before freezing the proposal plan, reserve the batch code:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_batch_code.py \
  --registry dataset/registry/batch_code_reservations.json \
  --batch-id <generation-batch-id> \
  --session-id <generation-session-id> \
  --created-at <YYYY-MM-DDTHH:MM:SSZ> \
  --output path/to/batch-code-reservation-receipt.json
```

After the repository-wide uniqueness receipt passes, reserve task IDs before
any task-root write:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_v1_task_ids.py \
  --registry dataset/registry/task_id_reservations.json \
  --plan path/to/task-id-plan.json \
  --uniqueness-receipt path/to/pre-generation-uniqueness.json \
  --batch-code-receipt path/to/batch-code-reservation-receipt.json \
  --output path/to/task-id-reservation-receipt.json
```

If any candidate ID is already registered or claimed, do not generate under
that ID. Same-session exact retries resume the existing reservation;
different-session or changed-proposal collisions must receive new IDs and
fresh uniqueness evidence.

## Generate and prove exact task roots

Invoke `$aider-sft-task-creator`. Derive the required public API and
starter-to-target file delta before materialization. If the starter header
lacks or misdeclares a required symbol, make that header editable and require
its target edit. Never infer source-only scope from a nonempty starter.

Immediately before creating each destination, verify its task ID and slot are
still `reserved` by the current session and proposal, and create the directory
with exclusive semantics. An existing destination or ownership mismatch fails
without overwrite.

Every task must have one digest-bound receipt proving:

- exact public namespace, symbol, signature, type, template, and qualifier
  visibility through a public-API compile probe;
- isolated-header strict C++17 warnings-as-errors compilation;
- target Weighted45 exactly 1.0;
- starter rejection for the intended reason;
- direct diagnosed-failure mutation rejection;
- distinct compiling semantic mutation rejection;
- protected-file integrity and required companion-file completeness;
- repeated grader determinism and GCC/Clang portability;
- ASan/UBSan and applicable concurrency checks;
- anti-reward-hacking checks and a dynamic per-run nonce; and
- production whole-file parse/application with exact final hashes.

Then rerun repository-wide uniqueness against all active, archived, imported,
staging, rejected, temporary, historical, fixture, linked-worktree, and
manifest-referenced task artifacts. Any match or incomplete scan fails.

Run the cumulative validator with `--stage post-generation`.

## Independently audit and repair

Invoke `$audit-sft-data-quality` read-only on the exact generated tree. Give the
auditor raw artifacts, not a desired verdict. Preserve subject hash, stable
finding IDs, evidence, and dispositions.

For each finding, invoke `$aider-task-family-remediation`, repair the owning
source, regenerate the complete affected family, refresh all evidence, and
obtain a fresh independent audit. Creator self-checks cannot close the
independent audit loop.

## Project and admit the corpus

Invoke `$aider-tasks-sft-dataset` only for digest-bound
`local_family_verified` roots. Generate private `pre.jsonl` and final
`train.jsonl` through the approved projector.

Require one per-row serialization receipt proving exact production tokenizer,
chat template, token IDs, loss mask, EOS, no truncation, whole-file parsing,
editable/protected scope, target hash, applied final state, and zero private
leakage.

Validate the complete topic with V1 and the count-matched baseline. Run the
required non-certifying `generic_cpp` Validator V2 analysis, read every task's
CSV/JSON feedback, repair through owners, regenerate, and repeat. Rebuild and
validate the complete merged corpus before release; require full-corpus V2
Platinum for a V2 certification claim.

Run Generator Admission V4.1 with `--stage pre-training`. A PASS authorizes only
the bounded canary, not a full run.

## Canary, promote, and certify deployment

Re-evaluate the previous-best checkpoint first if its attempt ledger is
missing. Run exactly 20 canary tasks for 5 epochs with at least four frozen
matched trials and the same harness, tasks, tests, tokenizer/template,
inference settings, seeds or declared seed policy, turn contract, and redacted
feedback policy. Log training loss, validation loss, compile rate, and
hidden-test rate at every checkpoint; early-stop and select by the frozen
40/40/20 composite policy.

Stop when any of these occurs:

- mean Pass@1 drops by more than one task;
- public-API-absent failures rise by more than two percentage points;
- contamination is nonzero;
- a required action topology is absent;
- malformed output or infrastructure failure is nonzero; or
- context exhaustion exceeds 1%.

Promotion requires compile and link >=98%, public API exposure >=97%,
semantic failures <=5%, runtime failures <=1%, header reconstruction >=95%,
shadow hidden tests >=90%, non-zero evaluation rows, strict Pass@1 improvement,
a complete matched transition matrix, exact exposure, strengthened Baseline 3,
and a recomputed score >=95. Training completion and near-zero loss are never
promotion proof. Run Generator Admission V4.1 with `--stage promotion`.

Promotion does not authorize deployment. Require consumer, manifest, model
card, rollback, monitoring, security, and reproducibility proof, then run
`--stage deployment`. The resulting local receipt does not claim an external
organizational signature.

## Preserve evidence and report truthfully

Keep immutable revision snapshots and bind owner/source, root, task proofs,
audit, pre/final JSONL, policies, compiler/image, tokenizer/template, canary,
and evaluation bytes by digest.

Use this claim ladder:

```text
failure_evidence_valid
-> generation_v4_authorized
-> candidate_generated
-> generated_task_v4_verified
-> local_family_verified
-> producer_projection_verified
-> baseline3_content_certified
-> v2_profile_platinum
-> curriculum_v4_1_validated
-> training_v4_1_admitted
-> canary_v4_1_passed
-> dynamics_v4_1_verified
-> consumer_verified_sft_ready
-> checkpoint_promotion_v4_1_passed
-> local_deployment_v4_1_certified
```

Report confirmed counts, invalid evidence, selected/replaced/rejected/review
rows, hard-failure IDs, exact hashes, unresolved blockers, and next gate.

## Validate CHARM changes

After changing this skill, run:

```bash
python3 /home/ubuntu/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .agents/skills/charm-skill

python3 .agents/skills/charm-skill/scripts/validate_generation_readiness.py \
  --list-rules

python3 -m pytest -q \
  tests/test_charm_generation_readiness.py \
  tests/test_charm_task_generation_v1_protocol.py \
  tests/test_charm_batch_code_reservations.py \
  tests/test_charm_task_id_reservations.py
```

Run repository-specific skill and documentation tests when their supporting
framework is present. A green skill validator proves structure only; it does
not prove task, corpus, consumer, or checkpoint quality.
