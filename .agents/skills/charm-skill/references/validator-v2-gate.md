# Validator V2 Gate

Read this reference before Charm projects, merges, certifies, or releases a
JSONL dataset. Task-root-only creation or local family remediation stops before
this gate and must not claim serialized dataset certification.

## Authority and activation

Validator V1 remains the authoritative serialized-row and Baseline-3 content
gate. Validator V2 reruns V1 as `STAGE-04`, then adds deterministic semantic,
curriculum, topic, benchmark, analytics, scoring, certification, reporting, and
manifest stages.

Apply these rules:

- Require a complete `generic_cpp` V2 analysis for every projected 20-task
  Charm topic before enqueueing it. Treat cross-topic gaps as inputs to the
  corpus coverage plan, not as proof that an otherwise valid topic batch is
  defective.
- Require a fresh `generic_cpp` V2 run over the entire rebuilt corpus before a
  dataset certification or release claim, and require that run to reach
  Platinum.
- Add benchmark profiles such as `fixed26` only when the authorized deliverable
  includes that benchmark certification. Never infer a benchmark profile from
  topic names.
- Keep V2 separate from tokenizer, template, loss-mask, context, split, loader,
  training, and empirical benchmark evidence.

## Preflight and execution

Verify the installed rule/configuration/knowledge/plugin catalog before the
first V2 run and after any validator policy change:

```bash
uv run aider-task-validator verify-validator-v2
uv run aider-task-validator list-rules-v2
```

First obtain a clean V1 Baseline-3 run. Then execute V2 on the same complete
private/final pair; do not substitute the earlier V1 report because V2 must
bind its own Core result into the final manifest:

```bash
uv run aider-task-validator validate-v2 path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --out path/to/train.validation-v2 \
  --config configs/aider_task_validator/execution-v1.json \
  --v2-config configs/aider_task_validator/execution-v2.json \
  --baseline configs/aider_task_validator/aider-sft-topic-20-v1-baseline.json \
  --benchmark-profile generic_cpp
```

Use the exact-20 baseline only for a 20-row topic batch. Use the applicable
full-corpus V1 baseline when validating the rebuilt dataset. Add repeatable
`--benchmark-profile` arguments only for explicitly selected profiles.

Do not use `--no-compile`, `--no-sanitizer-compile`, disabled mandatory rules,
or debug mode for certification. Keep each output directory immutable; choose
a new run directory instead of `--force` when preserving evidence.

## Batch analysis and corpus pass contracts

For a single-topic 20-row batch, require successful completion through the
report and manifest stages, 20 reconciled semantic profiles, no fatal or Core
failure, and a persisted capability-gap/recommendation report. The CLI may
exit `2` because the broad `generic_cpp` profile correctly detects capabilities
that belong to other topics. Record that result as `batch_v2_analyzed`, never
as V2 certification, and carry its gaps into the full-corpus plan.

Treat the full-corpus V2 gate as passed only when all of the following hold:

1. The CLI exits zero and reports `V2 level PLATINUM`.
2. `certification_manifest.v2.json` records a complete final manifest with no
   fatal reconciliation finding.
3. Every selected benchmark profile is eligible; missing private fingerprints,
   runtime receipts, or locked-image identities fail closed.
4. All 14 stage checkpoints exist and the manifest/report hashes reconcile.
5. `semantic_profiles.jsonl` contains exactly one profile for each selected
   task ID, with no missing, extra, or duplicate identities.
6. Capability gaps, token dominance, semantic redundancy, generalization risk,
   and profile findings satisfy the resolved V2 configuration across the full
   selected corpus.

Read at minimum:

- `evaluation_report.v2.json` and `unified_report.json`;
- `curriculum_report.json` and `curriculum_recommendations.json`;
- `benchmark_report.json` and `semantic_profiles.jsonl`;
- `certification_manifest.v2.json` and `certification_receipt.json`;
- `rule_graph.json`, stage/rule/capability/API CSVs, and `checkpoints/`.

The local receipt is intentionally unsigned. Never describe it as an
organization-signed certificate.

## Repair and invalidation

Recommendations never authorize automatic generation or mutation. Map each
actionable gap to the curriculum, generator/materializer, tests, renderer, or
selected manifest owner. Regenerate and independently audit the affected exact
roots, regenerate both JSONLs, rerun invalidated private/V1 gates, then rerun
V2 over the complete affected batch or corpus.

Changes to task bytes, admission, projection, V1 policy, compiler/image proof,
or private receipts invalidate V1 and downstream V2 evidence. Changes only to
V2 rules, taxonomy, knowledge base, plugins, configuration, or profiles
invalidate V2 reports and certification; rerun V1 as part of the V2 Core stage
but do not fabricate new private evidence when its bound subject is unchanged.

Never require a narrow topic to mimic a balanced whole corpus. Never reuse a
topic-batch V2 result as proof for the merged corpus, and never promote a V2
score, generalization-risk heuristic, or recommendation into an empirical
benchmark-uplift claim.
