# Failure-Conditioned Generation Gate

Treat the repository folder `updated task/audit-sft-data-quality/` as a
mandatory CHARM input for every request that creates a new task. This gate
authorizes synthesis; it does not replace creator proof, repository-wide
uniqueness, independent post-generation audit, V1/V2 validation, consumer
verification, or Generator Admission V4.

For the active SynthMem regression, also read and execute
`generator-admission-v4.md`. Its evidence bindings, API/action-topology profile,
genuine-repair policy, source-byte requirements, exposure gate, and bounded
canary are cumulative hard conditions.

## Resolve the exact authority

Locate the exact operator-supplied folder under the dataset workspace and read
these files completely:

- `SKILL.md`;
- `references/failure-conditioned-workflow.md`;
- `references/artifact-contracts.md`;
- `references/iterative-sft-data-design.md`; and
- `agents/openai.yaml`.

Record one deterministic tree SHA-256 over relative paths and bytes. Do not
silently substitute `.agents/skills/audit-sft-data-quality/` merely because it
has the same skill name. The latter remains CHARM's independent read-only
post-generation auditor; both gates are required. A missing, unreadable,
partially copied, or changed folder invalidates authorization and stops work as
`not_completed`.

## Pre-generation hard pass

Before designing or materializing a new task:

1. Freeze the iteration and evaluation contracts required by Phase 0 and Phase
   1 of the supplied skill.
2. Validate evaluator health and freeze the accepted evidence set. Require
   every expected task and attempt to have reconciled identity, terminal
   status, candidate artifacts, feedback/channel routing, environment, and
   oracle completion.
3. Build the atomic attempt, turn, and test-reachability ledgers. Never treat an
   unexecuted or unreachable test as an observed failure.
4. Produce one failure packet per underlying task with direct or sufficiently
   discriminating evidence for the causal mechanism.
5. Require `synthesis_disposition: synthesize`. Any `probe-first`,
   `eval-repair`, `eval-only`, `reject`, unresolved diagnosis, invalid
   evaluator, or unsupported general weakness blocks generation.
6. Complete oracle-first synthesis planning before target generation. Each
   proposed task must name an observable contract, meaningful oracle delta,
   protected/editable artifacts, held-out exclusions, provenance, and three
   negative controls: starter, diagnosed failure class, and a distinct
   compiling or executable semantic error.
7. Pass every frozen proposal to
   `repository-wide-uniqueness-gate.md`. Synthesis authorization cannot override
   a duplicate, near-duplicate, lineage, split, or contamination failure.
8. Freeze a synthesis-authorization receipt and verify its hash immediately
   before the owner or materializer writes candidate task bytes.
9. Populate a real copy of
   `../assets/charm-generator-admission-v4.template.json` and run
   `../scripts/validate_generation_readiness.py --stage pre-generation`.
   Require exit `0`, decision `PASS`, and zero hard-failure IDs.

The unchanged example template, a missing previous-best attempt ledger, zero or
insufficient existing-header edit coverage, an all-synthetic plan, raw private
feedback, missing exact source bytes, or a missing bounded-canary plan is an
unconditional stop.

When the request is not backed by accepted evaluation evidence and an
authorized failure-conditioned synthesis plan, do not invent a rationale or
generate a general curriculum task. Stop as `not_completed` and list the
missing evidence.

## Required synthesis decision receipt

Bind the synthesis-authorization receipt to:

- the supplied audit folder tree SHA-256 and file inventory;
- iteration, evaluation, accepted-run, attempt/turn, reachability, failure
  packet, and synthesis-plan hashes;
- task IDs, observed mechanisms, evidence tiers, and synthesis dispositions;
- held-out task/test/template/revision inventories and exclusion hashes;
- per-proposal contract, oracle delta, negative-control, and provenance hashes;
- repository-wide uniqueness receipt and proposed-task plan hash;
- an explicit zero count for invalid evidence, unresolved diagnoses,
  unauthorized dispositions, missing controls, and duplicate/contamination
  blockers; and
- decision `PASS`, policy version, owner, and receipt SHA-256.

Only PASS authorizes task ID reservation and materialization. Scores, warnings,
model-judge approval, or operator preference cannot override a failed
deterministic condition.

Two independent pre-generation receipts are required and must bind the same
proposal-plan hash:

1. the synthesis-authorization receipt defined here; and
2. the Generator Admission V4 pre-generation receipt.

Neither receipt can substitute for the other.

## Continue after generation

The pre-generation passes prove only that synthesis is evidence-authorized,
unique, correctly shaped, and planned. After generation, continue the supplied
skill's executable target, negative-control, exact serialization, lineage,
contamination, corpus, training, and held-out promotion phases.

Run Generator Admission V4 again at `post-generation`, `pre-training`, and
`promotion`. Every stage is cumulative. Re-run affected stages whenever the
evaluation evidence, proposal, oracle, task bytes, serialization, lineage,
audit-folder bytes, source bindings, feedback policy, or repository corpus
changes.

A post-generation failure cannot be grandfathered by an earlier PASS. Repair
through the owning source, regenerate, and obtain fresh receipts. Full training
remains unauthorized after `pre-training` PASS until the separate 1-3 epoch
canary passes; a failed canary terminates the iteration rather than weakening
the gate.
