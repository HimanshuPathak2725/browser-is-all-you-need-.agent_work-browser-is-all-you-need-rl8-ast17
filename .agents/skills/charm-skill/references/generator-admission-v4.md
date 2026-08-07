# CHARM Generator and Admission V4

Read this reference before authorizing any new CHARM task generation and again
before generated tasks, projected SFT rows, a training run, or a checkpoint move
to the next state. This policy is cumulative and fail-closed.

> V4.1 overlay: read
> [training-admission-promotion-v4-1.md](training-admission-promotion-v4-1.md).
> Its 20-30% repair ratio, 5-8% calibration ratio, editable-layout and starter
> targets, 20-task/5-epoch canary, absolute promotion metrics, strengthened
> baselines, and deployment stage supersede the older ranges in this base V4
> reference. All unaffected V4 task, oracle, uniqueness, security,
> serialization, and receipt rules remain mandatory.

## Contents

- [Purpose and active failure profile](#purpose-and-active-failure-profile)
- [Four cumulative decisions](#four-cumulative-decisions)
- [Complete pipeline](#complete-pipeline)
- [Pre-generation input contract](#pre-generation-input-contract)
- [Hard pre-generation gates](#hard-pre-generation-gates)
- [Generator obligations](#generator-obligations)
- [Post-generation task receipt](#post-generation-task-receipt)
- [Pre-training serialization and corpus gate](#pre-training-serialization-and-corpus-gate)
- [Canary and promotion gate](#canary-and-promotion-gate)
- [Validator commands](#validator-commands)
- [Manual sign-off checklist](#manual-sign-off-checklist)
- [Required negative regressions](#required-negative-regressions)
- [Claim boundaries](#claim-boundaries)

## Purpose and active failure profile

The active remediation profile is
`synthmem-v3-modal-eval4-20260803T054055Z`. It remains mandatory until a
matched, receipt-backed promotion evaluation proves that the targeted failure
has been corrected without unacceptable regression.

Bind these exact observations:

| Observation | Count |
| --- | ---: |
| Actual attempts | 311 |
| Failed attempts | 288 |
| Compile/link failures | 281 |
| Required public API absent or misnamed | 264 |
| Semantic counterexamples | 6 |
| Runtime/sanitizer failures | 1 |
| Existing-header changes in training | 0 |
| Genuine repair trajectories in training | 0 |
| Calibration rows in training | 0 |

The primary causal hypothesis is:

```text
nonempty starter -> protect header -> emit source only
                                      |
                                      v
evaluation requires missing public API in existing header
                                      |
                                      v
tests cannot compile
```

Do not interpret all 264 API diagnostics as proof of an untouched header. They
prove that the required API was not visible to the test translation unit; the
underlying defect may be an untouched, misplaced, misnamed, or incorrectly
qualified declaration. The intervention and oracle must distinguish those
mechanisms.

## Four cumulative decisions

The validator exposes four cumulative stages:

| Stage | Question | Authorized next action |
| --- | --- | --- |
| `pre-generation` | Is synthesis supported, unique, correctly shaped, fully planned, and atomically ID-reserved? | Materialize only the owner session's reserved candidates. |
| `post-generation` | Did every exact generated task pass API, oracle, grader, safety, application, and uniqueness proof? | Independently audit and project candidates. |
| `pre-training` | Did every loss-bearing row and the complete corpus pass admission? | Launch only the bounded canary. |
| `promotion` | Did the canary and matched evaluation pass? | Promote the checkpoint or proceed to an explicitly authorized full run. |

Every later stage reruns all earlier checks. A PASS is scoped to its exact
subject hash and stage. No earlier PASS survives a changed proposal, task,
oracle, test, source, policy, row, tokenizer, template, corpus, or evaluation.

## Complete pipeline

```text
0. Freeze previous-best control and exact attempt ledger
   |
1. Validate evaluation and post-run evidence
   |-- invalid evaluator ------------------------------> STOP not_completed
   |-- unresolved mechanism ---------------------------> STOP probe-first
   v
2. Build task failure packets and active remediation profile
   |
3. Freeze falsifiable iteration contract
   |-- target behavior
   |-- causal hypothesis
   |-- planned data intervention
   |-- primary metric and promotion threshold
   |-- regression budget and stop condition
   |-- authorized training diff
   |-- redacted feedback policy
   v
4. Freeze corpus and action-topology plan
   |-- 50-70% direct verified successes
   |-- 15-25% boundary cases
   |-- 10-20% genuine repair trajectories
   |-- 5-10% calibration
   |-- <=25% empty starters under active remediation policy
   |-- >=30% existing-header modifications
   |-- >=5% header-only/template actions
   |-- >=20% coordinated header+source actions
   |-- <=60% any one action shape
   |-- >=2 action topologies and one scaffold per family
   v
5. Bind exact builder/verifier/eval/tokenizer/template/policy bytes
   |
6. HARD PASS: repository-wide uniqueness before generation
   |-- task IDs
   |-- exact and normalized contracts
   |-- API graphs
   |-- code AST/CFG and solution structure
   |-- tests/mutations/oracles
   |-- semantic behavior
   |-- any match, ambiguity, parse failure, or incomplete scan -> STOP
   v
7. Atomically reserve task IDs and batch/topic slots
   |-- one canonical append-only registry and lock
   |-- repository-global ID absence
   |-- owner session, proposal, corpus index, and plan binding
   |-- collision, foreign claim, stale identity evidence -> STOP
   v
8. Run pre-generation V4 validator, including ID-000..002
   |-- FAIL --------------------------------------------> STOP not_completed
   v
9. Materialize exclusively through the owner generator/session
   |
10. Per-task proof
   |-- public API compile probe
   |-- isolated-header strict C++17 build
   |-- target Weighted45 exactly 1.0
   |-- starter rejected for intended reason
   |-- diagnosed failure mutation rejected
   |-- distinct compiling semantic mutation rejected
   |-- protected artifacts unchanged
   |-- repeated grader determinism and GCC/Clang portability
   |-- ASan/UBSan and applicable concurrency checks
   |-- anti-cheat and dynamic nonce checks
   |-- whole-file parse/application and companion-file completeness
   v
11. HARD PASS: repository-wide uniqueness after generation
    |
12. Run post-generation V4 validator
    |-- FAIL -------------------------------------------> owner repair/regenerate
    v
13. Independent read-only task audit
    |-- findings ---------------------------------------> owner repair/regenerate
    v
14. Project private pre.jsonl and final train.jsonl
    |
15. Exact production serialization replay per row
    |-- tokenizer and chat template
    |-- token IDs, loss mask, EOS, no truncation
    |-- production whole-file parser
    |-- editable/protected scope and final applied hashes
    |-- zero hidden/private leakage
    v
16. Corpus admission
    |-- one row per selected task
    |-- roles proved from content
    |-- defective ancestors replaced
    |-- six-level dedup/contamination
    |-- origin/family/action/explanation caps
    |-- anchor effective exposure preserved or explicitly canaried
    |-- V1 Baseline 3 pass
    |-- required V2 topic analysis reconciled
    v
17. Run pre-training V4 validator
    |-- FAIL -------------------------------------------> repair/rebuild
    v
18. Train 1-3 epoch or first-checkpoint canary only
    |-- evaluation rows must be logged
    |-- four frozen matched trials
    |-- redacted feedback policy matches training
    |-- compile reachability and public API completeness
    |-- pass@1 and conditional repair
    |-- format/context/infra health
    v
19. Apply automatic stop conditions
    |-- pass@1 drop >1 task ----------------------------> REJECT
    |-- public-API absence increase >2 pp -------------> REJECT
    |-- any contamination -----------------------------> REJECT
    |-- missing action topology -----------------------> REJECT
    |-- malformed or infrastructure failure ----------> REJECT
    |-- context exhaustion >1% ------------------------> REJECT
    v
20. Matched held-out promotion evaluation
    |-- fail->pass, pass->fail, stable pass/fail, mechanism changes
    |-- no comparison between raw-private and redacted feedback lanes
    v
21. Run promotion V4 validator
    |-- PASS -> authorize declared next stage
    `-- FAIL -> preserve evidence, reject checkpoint, revise hypothesis
```

## Pre-generation input contract

Copy `assets/charm-generator-admission-v4.template.json` into the iteration
workspace. The template deliberately has `example_only: true` and placeholder
hashes, so it cannot pass unchanged.

Bind the exact post-run artifacts with these required SHA-256 values:

| Binding | SHA-256 |
| --- | --- |
| `audit_summary` | `b2553fe505bbecd4420159deb7e070f30b3da71c8b1e5ff224b69a96a9c54f90` |
| `detailed_audit` | `4876a032875f0a31773bcc79d949d95131effaf8213ae9213953b4963c0f1ca6` |
| `validator_v4_spec` | `55ef7e69fb0a6d7f2d861ee761407f15971fb2fd0b28354d31e70cef11aaaef8` |
| `mechanism_summary` | `52e6b1581e86e7bdd5fbee8f5ec583ef17e9906dab56e57ffc95cca3c4c2c7a6` |
| `dataset_shape` | `6edba0c806293ab3a788434edba61ebd9bffb2506321d6d0f1191646be9a246b` |
| `training_dynamics` | `6f0bf263cb883930ebf3505c435f407ffa36e1fecbc05816050d56f09c0028e8` |

Also bind the deterministic tree hash of the exact operator-supplied
`updated task/audit-sft-data-quality/` folder. A similarly named installed or
repository skill is not a substitute.

Required source bindings are exact files, not hashes without bytes:

- builder source;
- verifier source;
- evaluation wrapper source;
- redacted feedback-policy source;
- tokenizer manifest;
- chat-template bytes;
- held-out manifest;
- atomic batch-code reserver source;
- atomic task-ID reserver source; and
- repository-wide uniqueness scanner source.

Relative binding paths resolve from the admission-bundle directory. Repeated
single-character placeholder digests are invalid.

## Hard pre-generation gates

### Evidence and iteration

- Require valid evaluator health with zero invalid evidence.
- Require zero unresolved diagnoses and zero unauthorized synthesis dispositions.
- Require the active failure-profile ID, exact counts, and exact artifact bytes.
- Require a previous-best attempt-ledger hash. If the historical ledger is
  missing, re-evaluate the previous-best checkpoint before generation.
- Require an explicit iteration contract and authorized training diff.

### Content-derived mixture

Roles are mutually exclusive and proved from content:

- `direct_verified_success`: final verified first-pass target;
- `boundary_case`: target with a distinct, hash-bound boundary/oracle delta;
- `repair_trajectory`: task, actual failing candidate, declared feedback, and
  corrected target with bound fail/pass receipts;
- `calibration`: oracle-backed no-change, clarification, or scope-preservation
  decision.

Metadata labels do not establish a role.

### Corrective action topology

Under this active profile, enforce:

```text
empty starter fraction                 <= 0.25
existing header changed fraction       >= 0.30
header-only or template fraction       >= 0.05
coordinated header+source fraction     >= 0.20
largest single action-shape fraction   <= 0.60
unparseable targets                    == 0
unjustified no-op targets              == 0
```

The generic V4 minimum for existing-header changes is 15%; this remediation
profile deliberately raises it to 30% because missing public API exposure was
the dominant causal failure. Retire the stronger threshold only through a new
policy version after matched promotion evidence.

### Feedback and repair

Use `redacted-compiler-feedback-v1` for training and promotion. Redact private
test paths, private test names, assertion bodies, expected values, and hidden
case structure. Public contract identifiers already present in the user task
may remain. Keep full private output only in a separately labeled internal
diagnostic lane.

Every repair row must prove:

```text
user(task)
assistant(actual failing candidate)
user(feedback emitted by the declared redaction policy)
assistant(corrected candidate)
```

Require the first candidate to fail for the declared mechanism and the second
to pass every task oracle. Do not count historical-failure metadata as a repair
trajectory.

### Required failure mechanisms

The generation plan must cover all of:

1. public API completeness;
2. file-action selection;
3. header self-containment;
4. compiler-feedback repair;
5. state-transition ordering;
6. container/object lifetime;
7. member/local shadowing;
8. warning-as-error discipline;
9. whole-file response application and termination; and
10. successful-anchor retention.

Generate mechanism-level independent contracts, not renamed benchmark clones.

### Atomic batch-code and task-ID admission

Before proposal freeze, reserve one permanent exactly five-digit batch code
through `batch-code-identity.md`. Bind its UTC timestamp, derivation, collision
probe, owner session, registry hashes, and receipt into all later plans.

Freeze one task-ID plan containing one unique repository-global ID and one
batch/topic slot per authorized task. Bind the plan's `protocol_id`,
generation batch/session, proposal-plan, and complete uniqueness corpus-index
hashes. V1 additionally requires 51 claims across the exact frozen 17-topic
registry with slots `1`, `2`, and `3` once per topic. After the repository-wide
zero-match receipt,
reserve the complete set under the one canonical append-only registry lock.

The admission bundle must include digest-bound
`batch_code_reservation_receipt`, `task_id_reservation_plan`, and
`task_id_reservation_receipt` files. Rules `ID-000..003` require a permanent
repository-unique five-digit batch code and zero
collisions, exact batch/session ownership, a one-to-one ID/slot set, registry
before/after hashes, and exact binding to the uniqueness receipt. Only an
unchanged `reserved` claim owned by the same session may resume. Every other
existing or terminal ID—including rejected and tombstoned IDs—is unavailable.
Never materialize before these rules PASS.

## Generator obligations

Before writing code, derive an explicit public API manifest and the
starter-to-target file delta.

If a required public symbol is missing or wrong in the starter, the header is
editable. A generator must never emit a “protect header/source-only” plan in
that situation. Reject contradictions among prompt editable files, starter
hashes, target files, expected public API, and applied output.

For every task, create:

- a public-API compile probe that includes the candidate header and exercises
  exact namespace, symbol, signature, type, template, and qualifier visibility;
- an isolated header translation unit under strict C++17 warnings-as-errors;
- the complete target/reference;
- a starter expected to fail for the intended reason;
- a direct mutation reproducing the diagnosed mechanism;
- a distinct compiling semantic mutation;
- deterministic grader tests repeated under the declared policy;
- GCC and Clang portability evidence where available;
- ASan/UBSan and applicable TSan evidence;
- anti-reward-hacking probes, including constructors/destructors, macro
  poisoning, standard-library shadowing, weak/alias/linker tricks, exit/signal
  interception, dynamic loading, and output/receipt spoofing;
- a per-run unpredictable nonce verified through the real grader path; and
- production whole-file parse/application replay with exact final file hashes.

Specific mutation families required by the active failure profile include:

- missing, misnamed, misplaced, or wrongly qualified public declaration;
- missing direct standard-library include;
- private member access or incompatible template/type arguments;
- unused parameter under `-Werror`;
- member/local shadowing that leaves object state uninitialized;
- destroying a link before reading the next/previous pointer;
- calling `reserve` and indexing elements that were never constructed; and
- exhausting the response budget without applying every required file.

## Post-generation task receipt

At `post-generation`, provide one object in `task_receipts` per authorized task:

```json
{
  "task_id": "topic/task-id",
  "role": "direct_verified_success",
  "action_topology": "header_and_source",
  "requires_public_api_change": true,
  "existing_header_changed": true,
  "target_passed": true,
  "weighted45": 1.0,
  "starter_rejected": true,
  "failure_mutation_rejected": true,
  "semantic_mutation_rejected": true,
  "protected_artifacts_unchanged": true,
  "api_probe_passed": true,
  "header_isolation_passed": true,
  "strict_cpp17_werror_passed": true,
  "grader_determinism_passed": true,
  "grader_portability_passed": true,
  "sanitizer_passed": true,
  "anti_cheat_passed": true,
  "dynamic_nonce_passed": true,
  "application_replay_passed": true,
  "required_companion_files_complete": true,
  "private_test_output_disclosed": false,
  "oracle_receipt_sha256": "sha256"
}
```

For repair rows, also require:

```json
{
  "genuine_four_turn_structure_passed": true,
  "failing_candidate_receipt_bound": true,
  "corrected_candidate_receipt_bound": true,
  "feedback_policy_match_passed": true
}
```

Counts and IDs are recomputed from receipts and must equal the frozen plan.
Then rerun repository-wide uniqueness against the exact generated bytes. Any
match or ambiguous near match is a hard failure.

## Pre-training serialization and corpus gate

Provide one serialization receipt per selected task:

```json
{
  "task_id": "topic/task-id",
  "exact_token_replay_passed": true,
  "loss_mask_passed": true,
  "eos_passed": true,
  "no_truncation": true,
  "whole_file_parse_passed": true,
  "proved_target_hash_match": true,
  "editable_scope_passed": true,
  "protected_scope_passed": true,
  "action_harmony_passed": true,
  "no_private_artifact_leakage": true,
  "token_ids_sha256": "sha256",
  "loss_mask_sha256": "sha256"
}
```

The corpus-admission summary must prove:

- task and serialization receipts reconcile one-to-one;
- exact, held-out, semantic ambiguity, and unresolved-review counts are zero;
- defective ancestors and corrected descendants do not coexist as positives;
- role, action, family, origin, and explanation-prefix caps pass;
- known-successful anchor exposure is not silently diluted;
- V1 Baseline 3 passes on the complete private/final pair; and
- the required V2 batch analysis is complete and reconciled.

Use:

```text
effective exposure = selected rows * epochs * sampling weight
```

If planned anchor exposure is lower than the previous successful run, require
both explicit iteration-contract authorization and a retention canary. Equal
total updates do not prove equal anchor exposure.

## Canary and promotion gate

Before a costly full run, train at most three epochs or stop at the first
predeclared checkpoint. Log held-out evaluation rows during training. Compare
against a freshly reconstructed previous-best attempt ledger under identical
harness, task/test hashes, tokenizer/template, model settings, trial IDs or
seeds, turn contract, and feedback policy.

Hard stop when:

- mean Pass@1 drops by more than one task;
- public-API-absent failures rise by more than two percentage points;
- contamination is nonzero;
- a required action topology is absent in canary generations;
- malformed output or infrastructure failure is nonzero; or
- context exhaustion exceeds 1%.

Promotion requires a complete matched transition matrix and separate counts for
compile reachability, API completeness, semantic failures, conditional repair,
malformed output, context exhaustion, timeout, and infrastructure failure.
Never use near-zero training loss as promotion evidence.

## Validator commands

Create a real admission bundle from the template. First atomically reserve
the batch code, then run repository-wide uniqueness, create the task-ID plan,
and atomically reserve it:

```bash
python3 .agents/skills/charm-skill/scripts/reserve_batch_code.py \
  --registry <dataset-root>/registry/batch_code_reservations.json \
  --batch-id <generation-batch-id> \
  --session-id <generation-session-id> \
  --created-at <YYYY-MM-DDTHH:MM:SSZ> \
  --output path/to/batch-code-reservation-receipt.json

python3 .agents/skills/charm-skill/scripts/reserve_v1_task_ids.py \
  --registry <dataset-root>/registry/task_id_reservations.json \
  --plan path/to/task-id-plan.json \
  --uniqueness-receipt path/to/pre-generation-uniqueness.json \
  --batch-code-receipt path/to/batch-code-reservation-receipt.json \
  --output path/to/task-id-reservation-receipt.json
```

Bind both files into the admission bundle, then run:

```bash
python3 .agents/skills/charm-skill/scripts/validate_generation_readiness.py \
  --stage pre-generation \
  --input path/to/charm-generator-admission-v4.json \
  --output path/to/pre-generation-receipt.json
```

After materialization, add `task_receipts` and the bound
`post_generation_uniqueness_receipt`, then run with
`--stage post-generation`.

After projection and corpus validation, add `serialization_receipts` and
`corpus_admission`, then run with `--stage pre-training`.

After the bounded canary and matched evaluation, add `canary_result` and
`promotion_result`, then run with `--stage promotion`.

Exit codes:

| Code | Meaning |
| ---: | --- |
| 0 | Every hard rule for the requested cumulative stage passed. |
| 1 | Input could not be read or parsed. |
| 2 | One or more deterministic hard rules failed. |

Every receipt includes stable rule IDs, observed and expected values, evidence,
reason, suggested remediation, deterministic confidence, subject hash, and the
exact next action. Do not manually edit a PASS receipt.

## Manual sign-off checklist

Before new task generation, a human reviewer must verify all of the following
against raw artifacts, not only the validator summary:

- [ ] The admission bundle is not the unchanged example template.
- [ ] The active failure-profile files match all six required digests.
- [ ] The exact updated-task audit-skill tree is present and hash-bound.
- [ ] The evaluator was healthy and all 311 attempts reconcile.
- [ ] The public-API diagnosis is described as visibility failure, without
      overclaiming that every header was untouched.
- [ ] A previous-best attempt ledger now exists and is hash-bound.
- [ ] The iteration contract changes only authorized variables.
- [ ] The role counts sum exactly and satisfy every range.
- [ ] Existing-header edits are at least 30% for this remediation iteration.
- [ ] Empty starters are at most 25%.
- [ ] Every family has two action topologies and an existing scaffold.
- [ ] At least one verified source is non-synthetic.
- [ ] Repair rows are genuine fail/feedback/correction trajectories.
- [ ] Feedback is redacted and identical between training and promotion.
- [ ] All ten required failure mechanisms have planned independent coverage.
- [ ] Repository-wide uniqueness scanned active, archived, imported, staging,
      rejected, temporary, historical, fixture, and linked task inventories.
- [ ] Every exact, near, structural, semantic, ambiguous, and parse-failure
      collection in the uniqueness receipt is empty.
- [ ] Every planned task ID is absent from all permanent/historical registries,
      ledgers, tombstones, task roots, JSONLs, and active reservations.
- [ ] One canonical batch-code lock permanently reserved the exact five-digit
      timestamp-derived code for this batch and session.
- [ ] One canonical shared-registry lock atomically reserved every planned ID
      and slot for this exact batch, session, proposal, and corpus index.
- [ ] A retry resumes only identical still-reserved claims owned by the same
      session; no terminal/tombstoned ID is reused or foreign claim taken over.
- [ ] Builder, verifier, evaluation wrapper, tokenizer, template, held-out
      manifest, policy, and scanner source bytes are packaged.
- [ ] Every planned proof has an owner and a repository-owned command.
- [ ] Anchor effective exposure is preserved or explicitly canary-protected.
- [ ] Full training remains blocked until the bounded canary passes.
- [ ] The pre-generation validator exits 0 and the reviewer independently
      inspects every rule record in the receipt.

Record reviewer identity, review time, admission-subject hash, receipt hash,
exceptions, and final `approve|reject|not_completed`. Manual approval cannot
override a failed deterministic rule.

## Required negative regressions

The CHARM validator and owning production validators must reject at least:

1. 50% empty-starter header+source rows plus 50% header-protected source-only rows;
2. zero existing-header modifications;
3. a repair-labeled row with only a final answer;
4. a repair row using private test output while promotion uses redacted feedback;
5. a missing public declaration with a source-only target;
6. a header using a standard-library type without its direct include;
7. a target passing semantics while the public API probe cannot compile;
8. a task with Weighted45 below exactly 1.0;
9. a static initializer, macro poison, symbol override, or static nonce bypass;
10. a tokenizer replay that changes a loss mask or truncates EOS;
11. a builder/verifier/wrapper digest with no packaged source bytes;
12. an exact, AST-near, oracle-near, or ambiguous repository-wide duplicate;
13. a corrected row coexisting with its defective positive ancestor;
14. a plan silently halving successful-anchor exposure;
15. an all-synthetic selected corpus;
16. a completed training run with no held-out evaluation rows;
17. a failed 1-3 epoch canary followed by a full training launch;
18. promotion using only aggregate historical scores without an attempt ledger;
19. a compile-blocked attempt counted as a semantic failure; and
20. a union across independent samples mislabeled as individual pass@k;
21. two sessions both passing reservation for the same task ID or batch/topic
    slot;
22. generation after an unlocked ID lookup without an atomic reservation
    receipt; and
23. reuse or takeover of a released, rejected, abandoned, expired, or
    tombstoned task ID;
24. two batches claiming the same five-digit code or a code assigned without
    the canonical atomic registry lock.

## Claim boundaries

Use the existing CHARM claim ladder and add these V4 states:

```text
failure_evidence_valid
-> generation_v4_authorized
-> candidate_generated
-> generated_task_v4_verified
-> local_family_verified
-> producer_projection_verified
-> baseline3_content_certified
-> v2_profile_platinum
-> pretraining_v4_admitted
-> canary_v4_passed
-> consumer_verified_sft_ready
-> checkpoint_promotion_v4_passed
```

`generation_v4_authorized` proves only that task synthesis may begin.
`generated_task_v4_verified` proves exact task packages, not SFT rows.
`pretraining_v4_admitted` permits only the bounded canary.
Only matched promotion evidence can establish empirical checkpoint improvement.
