# Continuous Aider SFT Quality Loop

Use this protocol when the requested outcome is a high-quality Aider C++ task
set plus private producer rows and final two-message SFT rows. It coordinates
existing creator, independent-audit, remediation, projection, and serialized-row
validation responsibilities. It does not transfer authority between them.

## Claim ladder

Use only the strongest status whose complete evidence exists:

| Status | Required evidence |
| --- | --- |
| `candidate_generated` | Owner-generated task root and source lineage |
| `creator_preflight_passed` | Structural, normal, sanitizer, negative-fixture, diversity, and contamination preflight |
| `local_family_verified` | Fresh independent audit of the exact regenerated tree with zero unresolved hard findings |
| `producer_projection_verified` | Authoritative private `pre.jsonl` and byte-exact deterministic comparison to final rows |
| `baseline3_content_certified` | Every final row and the whole corpus pass Progressive Baseline 3 |
| `consumer_verified_sft_ready` | Release contract, tokenizer/template, loss-mask, length, split, and consumer verification all pass |

`baseline3_content_certified` is not automatically
`consumer_verified_sft_ready`. On the current branch, which has no approved
release/projector or consumer pipeline, stop at the strongest available local
status and record the missing stage as `not_completed`.

## Required pipeline

Follow this state machine in order:

```text
freeze contract, holdout, inventory, and hashes
  -> plan a bounded capability-balanced batch
  -> design executable C++17 root contracts
  -> implement through the repository owner
  -> regenerate task roots
  -> creator preflight
  -> independent read-only audit
       findings -> remediation owner -> regenerate -> fresh audit (repeat)
       clean    -> freeze selected/replaced/rejected manifests
  -> render private pre.jsonl through an authorized owner
  -> deterministically project final train.jsonl
  -> compare source -> pre -> final and validate every row/corpus
       below Baseline 3 -> feedback -> owner repair -> restart at regeneration
       Baseline 3       -> downstream tokenizer/mask/consumer verification
  -> consumer_verified_sft_ready or truthful not_completed
```

Never skip backward invalidation. A prompt, starter, target, reference, test,
generator, renderer, compiler/image, verifier policy, or selected-manifest
change invalidates every downstream receipt derived from the old bytes.

## Phase 1: freeze the iteration contract

Before authoring, record:

- target behavior, public output contract, failure behavior, resource limits,
  and evaluation policy;
- base-eval weakness, expected mechanism, affected held-out capability, and a
  falsifiable uplift hypothesis;
- immutable benchmark holdout inventory and contamination fingerprints;
- source inventory, license/usage terms, lineage, revisions, hashes, and task
  counts;
- required task-family, API, file-layout, interaction, difficulty, and
  edge-case coverage cells;
- bounded authoring batches and backfill capacity.

For fixed-26-aligned work, apply the count, mix, first-try/repair, file-layout,
and family targets in `aider-fixed26-sft-improvement.md`. Counts never admit a
weak task: only verified roots satisfy a cell.

## Phase 2: design and create roots

For every root, write the executable contract before the reference:

- unique task ID plus new/replacement/parent lineage;
- exact public C++17 API and declared editable files;
- owned state and lifecycle, normal and invalid behavior, boundaries, ties,
  ordering, duplicates, and exception guarantees;
- visible prompt examples and private deterministic assertions;
- at least one coherent, warning-free plausible-but-wrong implementation that
  the production tests reject;
- clean-room provenance and the held-out capability it analogizes without
  copying official benchmark content.

Use `$aider-sft-task-creator`. Change only the repository generator,
materializer, curriculum, or focused tests; never hand-edit generated roots.
Generate complete starter files, complete private reference files, visible and
hidden tests, negative fixtures, role metadata, and digest-bound receipts.

## Phase 3: creator preflight and independent audit

Creator preflight must cover the exact complete family:

1. structure, role boundary, public-prompt leakage, filenames, and file roles;
2. strict warning-free C++17 normal build and deterministic tests;
3. fresh strongest available ASan/UBSan build and runtime tests;
4. compilation and rejection of every declared plausible-wrong fixture;
5. locked, network-disabled image sanity when the family contract requires it;
6. all-pairs diversity across mechanism, state, API, failure modes, file
   interaction, algorithms, and edge cases;
7. task-ID, lineage, prompt, answer/AST, semantic-family, and benchmark
   contamination screens;
8. digest binding for task, tests, reference, owner, image/compiler, policy,
   and results.

Then run `$audit-sft-data-quality` read-only against the raw exact tree. The
creator's preflight cannot self-admit a family. Preserve stable finding IDs and
the audit subject hash.

For every finding, use `$aider-task-family-remediation`: fix the owner or
contract, regenerate the complete affected family, invalidate old evidence,
rerun the full preflight, and request a fresh independent audit. Repeat while
safe in-scope repairs remain. Never weaken tests, baselines, or diversity rules
to force convergence. A real missing prerequisite ends as `not_completed`.

## Phase 4: freeze admission

After a clean fresh audit, write immutable selected, replaced, rejected, and
review manifests. Require one active selected version per task identity. A
same-ID revision stays quarantined until its new exact bytes independently
pass. The projector may consume only the selected manifest and current
digest-bound receipts.

## Private `pre.jsonl` contract

An authorized owner-controlled projector writes one private object per physical
line using `aider-sft-pre-row-v1`:

```json
{"schema_version":"aider-sft-pre-row-v1","task_id":"club-fund","label":"club-fund","introduction":"Implement a C++17 stateful fund.","instructions":"Implement the exact API and lifecycle behavior...","starter_files":[{"path":"club-fund.cpp","content":"#include \"club-fund.h\"\n"},{"path":"club-fund.h","content":"#pragma once\n..."}],"target_files":[{"path":"club-fund.cpp","content":"#include \"club-fund.h\"\n..."},{"path":"club-fund.h","content":"#pragma once\n..."}],"metadata":{"schema_version":"aider-sft-row-v1","task_id":"club-fund","root_task_id":"club-fund","task_family_id":"stateful-lifecycle","purpose":"primary-aider-sft-dataset","format":"aider-whole","subset":"train","language":"cpp","language_standard":"c++17","source_kind":"clean-room","source_revision":"owner-revision","source_row_format":"final-answer-only","renderer_version":"aider-whole-compact-v1","verification_status":"local_family_verified","editable_files":["club-fund.cpp","club-fund.h"],"tags":["stateful-lifecycle"]},"verification":{"status":"local_family_verified","subject_sha256":"<64 lowercase hex>","receipt_path":"<private receipt path>","receipt_sha256":"<64 lowercase hex>","normal":"pass","sanitizer":"pass","negative_fixture":"pass","contamination":"pass","duplicate_family":"pass","independent_audit":"pass"}}
```

Rules:

- Store the object on one physical UTF-8 JSONL line with unique keys.
- Treat `pre.jsonl` as private producer evidence; it may contain verified
  target files and private receipt locations, so never publish or train on it.
- Preserve exact task identity, public text, ordered file paths/content, safe
  final metadata, and receipt bindings.
- Do not store hidden-test bodies, secrets, credentials, or unrestricted host
  paths even in `pre.jsonl`; point to a private digest-bound receipt instead.
- Generate it from the selected manifest and task owners. Do not reconstruct it
  from final rows when authoritative provenance exists.

## Final `train.jsonl` contract

Project exactly one `aider-sft-row-v1` object per physical line:

````json
{"schema_version":"aider-sft-row-v1","task_id":"club-fund","label":"club-fund","messages":[{"role":"user","step_loss_mask":0,"content":"Use Aider whole edit format...\n\n# Introduction\n\n...\n\n# Instructions\n\n...\n\n# Editable starter files\n\nclub-fund.cpp\n```cpp\n...\n```\n\nclub-fund.h\n```cpp\n...\n```\n"},{"role":"assistant","step_loss_mask":1,"content":"club-fund.cpp\n```cpp\n...complete target...\n```\n\nclub-fund.h\n```cpp\n...complete target...\n```\n"}],"metadata":{"schema_version":"aider-sft-row-v1","task_id":"club-fund","root_task_id":"club-fund","task_family_id":"stateful-lifecycle","purpose":"primary-aider-sft-dataset","format":"aider-whole","subset":"train","language":"cpp","language_standard":"c++17","source_kind":"clean-room","source_revision":"owner-revision","source_row_format":"final-answer-only","renderer_version":"aider-whole-compact-v1","verification_status":"local_family_verified","editable_files":["club-fund.cpp","club-fund.h"],"tags":["stateful-lifecycle"]}}
````

Require exactly two messages, loss mask `0` then `1`, complete ordered editable
files, no system/demo/reset/acknowledgement transcript, and no tests,
references, receipts, private paths, metadata, reasoning, or prose in the
assistant output. The renderer must preserve public text and file bytes from
`pre.jsonl`; never patch final JSONL manually.

## Phase 5: validate source, pre, and final

Run the validator after every projection or regeneration:

```bash
uv run aider-task-validator validate path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --out path/to/train.validation \
  --baseline configs/aider_task_validator/aider-sft-row-v1-baseline.json
```

Require:

- strict UTF-8/JSON and exactly one accounted-for object per physical line;
- one-to-one task sets and exact label, metadata, introduction, instruction,
  ordered starter, and ordered target equality from `pre.jsonl` to final rows;
- no private verification value leaked into model-facing messages;
- complete row, Markdown, virtual-file, Tree-sitter AST, API, compile/link,
  sanitizer-instrumentation, cross-consistency, hallucination, and whole-corpus
  duplicate checks;
- current private runtime receipts for semantics and ASan/UBSan execution;
- downstream official-tokenizer/template/loss-mask/length checks before the
  final `consumer_verified_sft_ready` claim.

If no `pre.jsonl` exists, the validator writes
`pre_reconstruction.jsonl`. It is advisory, non-authoritative, never released,
and cannot establish producer provenance. The strongest possible claim in that
mode is `baseline3_content_certified`, assuming all other local gates pass.

## Progressive baselines

The baselines are cumulative:

| Gate | Baseline 1: Structural Validity | Baseline 2: High Quality | Baseline 3: Production Content |
| --- | ---: | ---: | ---: |
| Critical rules | 100% | 100% | 100% |
| Major rules | >=85% | >=92% | >=98% |
| Minor rules | >=80% | >=88% | >=95% |
| Certification ordinals | every metric >=3.0/5 | every metric >=4.0/5 | every metric >=4.5/5 |
| Compile/link | pass | pass | pass, warning-free |
| Sanitizer instrumentation | diagnostic | pass | pass plus current private runtime receipt |
| Metadata | structural | 100% | 100% |
| Cross consistency | structural | >=95% | 100% |
| Prompt / assistant | structural | certified rules | >=95% / >=98% |
| Hallucination | 100% | 100% | 100% |
| Duplicate gate | exact/corpus rules | pass, similarity <0.95 | pass under configured final thresholds, overall <0.90 |

Complexity metrics characterize and balance the corpus; they are not
certification-bearing by themselves. Do not inflate a task with unrelated
helpers to raise complexity. A weighted score never overrides any gate.

## Repair controller protocol

The validator remains read-only. It always writes the score dashboard and
repair evidence. A controller or repair agent may act only through task owners:

```text
evaluate exact dataset
  -> read dataset_scores.csv
  -> read improvement_feedback.json
  -> select only Baseline-3 failures
  -> preserve task identity and passing behavior
  -> repair contract/owner/tests/renderer as directed
  -> regenerate complete affected roots
  -> rerun private evidence and fresh independent audit
  -> regenerate pre.jsonl and train.jsonl
  -> evaluate exact complete dataset again
  -> repeat until every task passes Baseline 3 or a blocker is not_completed
```

Preserve `task_id`, `label`, root/family identity, and lineage unless the
finding explicitly proves an identity collision. Do not freeze stale revision,
hash, receipt, or verification metadata; those must change with new bytes.
Modify only what closes a finding, then rerun every invalidated downstream
gate. Never instruct the repair agent to return an unverified JSON object and
substitute that for owner regeneration.

## Revision and regression control

Keep immutable controller snapshots named `revision_0001`, `revision_0002`,
and so on outside the released dataset. Bind each snapshot to source/pre/final
hashes, owner revision, policy fingerprint, audit receipt, score, baseline,
and finding IDs. The validator's `revision_history.jsonl` is a score ledger;
`best_revisions.json` identifies the best-known hash. The validator does not
store source bytes or perform rollback. Restore only through the owning
generator or the controller's immutable snapshot, then rerun all invalidated
gates.

Stop only when every row is Baseline 3, corpus baseline comparison passes,
pre/final comparison passes when authoritative pre exists, and every required
private/downstream gate for the claimed status is current. Stop earlier with a
truthful `not_completed` blocker rather than looping without an actionable,
authorized repair.

## Required run artifacts

Retain at least:

- source, selected, replaced, rejected, and review manifests with hashes;
- independent audit and remediation-cycle records;
- digest-bound normal/sanitizer/negative-fixture/contamination receipts;
- private authoritative `pre.jsonl` and final `train.jsonl` hashes;
- `dataset_scores.csv`, `evaluation_report.json`,
  `evaluation_report.md`, `evaluation_report.html`, `failed_rules.csv`,
  `dataset_summary.json`, `improvement_feedback.json`,
  `pre_comparison.json`, optional advisory `pre_reconstruction.jsonl`,
  `revision_history.jsonl`, and `best_revisions.json`;
- tokenizer/template/loss-mask/length and consumer verification evidence when
  claiming `consumer_verified_sft_ready`.

Keep generated task roots, JSONL, snapshots, receipts, and reports in ignored
local artifact roots unless the user separately authorizes an export.
