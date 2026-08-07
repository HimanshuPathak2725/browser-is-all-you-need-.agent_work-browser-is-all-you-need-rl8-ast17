---
name: audit-sft-data-quality
description: Audit, iteratively improve, and certify supervised fine-tuning datasets against the behavior and task they are meant to teach. Use when inspecting or validating generated SFT JSONL, private producer pre.jsonl, chat messages, instruction-response pairs, tool or agent trajectories, code corpora, synthetic examples, revised datasets, base-model evals, pass@k skill maps, train-validation-test splits, benchmark contamination, duplicate lineage, answer correctness, token limits, data mixtures, progressive baselines, or train-readiness claims. Produce an evidence-backed row catalog, quality gates, repair feedback, duplicate and contamination report, corpus composition analysis, and a truthful train, review, replace, reject, eval-only, content-certified, or consumer-ready decision.
---

# Audit SFT Data Quality

## Core rule

Judge every row against the target task. A polished answer is not high-quality
supervision if it teaches the wrong behavior, violates the task contract, leaks
the evaluator, or cannot be verified.

Apply hard correctness and integrity gates before diversity scores, confidence
scores, or aesthetic judgments.

When invoked by `$aider-sft-task-creator`, keep the audit read-only. Write
stable finding IDs and immutable dispositions for the exact audit subject. Send
all actionable findings to `$aider-task-family-remediation`; after regeneration,
rerun this audit from raw evidence against the new exact tree. A remediation
self-check cannot close an audit finding, and a prior clean report is stale
after any artifact or policy change.

For base-eval diagnosis, capability planning, synthesis, augmentation, and
iterative dataset design, read
[iterative-sft-data-design.md](references/iterative-sft-data-design.md).

For Aider Polyglot C++ fixed-26 SFT improvement or any local Aider batch
derived from that eval, also read
[aider-fixed26-sft-improvement.md](references/aider-fixed26-sft-improvement.md).
Treat those findings as an eval-shaped corpus gate, not merely optional
recommendations.

For an end-to-end Aider task-generation, private-producer, final-JSONL,
validation, repair, and certification request, read and follow
[continuous-aider-sft-quality-loop.md](references/continuous-aider-sft-quality-loop.md)
completely. It is the exact orchestration contract for `$aider-sft-task-creator`,
this independent audit, `$aider-task-family-remediation`, an authorized
owner-controlled projector, and the read-only row validator.

## Aider continuous quality state machine

Keep these responsibilities separate:

```text
creator owns contract + generator + preflight
auditor owns independent findings + dispositions
remediator owns source fixes + regeneration + private reverification
projector owns deterministic pre.jsonl + train.jsonl bytes
validator owns read-only row/corpus scores + feedback + revision ledger
consumer verifier owns tokenizer/template/loss-mask/length proof
```

Do not let one stage self-certify the next. After any actionable validator
failure, repair only through the relevant owner, regenerate the task tree and
both projections, obtain a fresh independent audit, and validate the exact
complete dataset again. Continue until every retained row passes Progressive
Baseline 3 or record a concrete `not_completed` prerequisite. Never weaken a
gate or allow a weighted score to force convergence.

Use this truthful claim ladder:

```text
candidate_generated
-> creator_preflight_passed
-> local_family_verified
-> producer_projection_verified
-> baseline3_content_certified
-> consumer_verified_sft_ready
```

On this branch, no approved release projector or tokenizer/mask consumer
pipeline is shipped. A local validation pass may establish
`baseline3_content_certified`; it may not by itself establish
`consumer_verified_sft_ready`.

## 1. Define the behavior contract

Write the contract before reading candidate answers:

| Field | Required description |
| --- | --- |
| Task | What the model must accomplish |
| Inputs | Allowed data, context, tools, and state |
| Output | Required schema, format, files, actions, or response style |
| Invariants | Facts that must remain true |
| Failure behavior | Rejection, abstention, rollback, or recovery rules |
| Resource limits | Context, tokens, latency, memory, calls, or complexity |
| Evaluation | Oracle, tests, rubric, benchmark, and sampling policy |
| Generalization target | Novel domains, templates, difficulty, or workflows |

Do not infer train readiness while any contract-critical field is unknown. Record
assumptions explicitly when the source does not define them.

## 2. Freeze the source inventory

Preserve immutable evidence before transforming data:

- source path, repository, revision, archive member, or URL;
- file and member SHA-256;
- row counts and unique task counts;
- schema version and split;
- synthetic, human, model-generated, repaired, or imported provenance;
- license, privacy, consent, and secret-handling constraints;
- parent row or revision lineage.

Never overwrite raw inputs. Put normalized, selected, repaired, and rejected
rows in separately identified artifacts.

### Pre-merge admission rule

Do not create a training mixture by appending parsed, review-only, or merely
plausible rows. Before a row can enter a selected manifest, require a
digest-bound admission receipt for its exact prompt and target that records:

- an executable behavioral contract and the assertions covering each material
  requirement;
- an independent oracle outcome, including strict build/test/sanitizer evidence
  for code when applicable;
- at least one executed plausible-but-wrong discriminator or mutation that the
  task rejects;
- task identity, source/revision lineage, and an explicit parent,
  replacement, or new-root relation;
- source, prompt, target, test/oracle, compiler/image, and verifier-policy
  digests.

Any content or environment change invalidates the receipt. Quarantine a
same-ID revision until it is independently verified; never train it beside a
trusted ancestor as an unrelated target. Missing evidence is `review`, not
implicit admission. A corpus builder must consume only the selected manifest
and must fail on duplicate IDs, conflicting lineage, duplicate prompt/answer
hashes, or contamination-screen failures.

## 3. Validate structure and conversation semantics

Check every row, not a sample:

- parseability and required keys;
- stable task identity and label consistency;
- legal role order and nonempty assistant target;
- output-format compliance;
- tool-call and tool-result pairing;
- referenced files, attachments, schemas, and environments;
- absence of accidental test, reference-answer, private-state, or system-prompt
  content;
- tokenizer-measured length under the actual model revision;
- loss masking and target boundaries when the training loader uses them.

Reject malformed rows rather than silently coercing them unless the repair is
deterministic, recorded, and reverified.

### Mandatory post-generation baseline gate

After every Aider SFT JSONL generation or regeneration, validate the exact
complete file with the repo-owned validator. Never validate a sample and infer
the state of the remaining rows. Validate every physical row before continuing:

```bash
uv run aider-task-validator validate path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --out path/to/train.validation \
  --baseline configs/aider_task_validator/aider-sft-row-v1-baseline.json
```

Require all of the following before handoff, selection, mixture construction,
or any train-readiness statement:

- every physical JSONL line is accounted for by exactly one task evaluation;
- every row passes the critical, major, minor, and ordinal certification gates;
- warning-free C++17 compile/link and sanitizer-instrumentation checks run
  rather than being disabled;
- the corpus-wide exact/AST/near-duplicate pass covers the entire dataset;
- the exact dataset meets or exceeds every versioned baseline threshold;
- the report SHA-256 binds the bytes that will be handed off;
- each `verification_status` remains backed by the current private digest-bound
  build/test/sanitizer and plausible-wrong-discriminator receipt.
- every task passes cumulative Baselines 1, 2, and 3, and
  `improvement_feedback.json` has no remaining task entries;
- authoritative `pre.jsonl`, when available, maps one-to-one and byte-exactly
  to the final public text, starter files, target files, identity, and metadata;
- revision history identifies the current and best-known content hashes, while
  rollback remains an owner/controller action rather than a validator edit.

Treat exit code `2`, any failed baseline comparison, omitted row, skipped
compiler gate, stale report hash, or post-report row change as `not_completed`.
A weighted score never overrides a certification failure. `--no-compile` and
`--no-sanitizer-compile` are diagnostics only and cannot close the gate.

Read `docs/AIDER_TASK_VALIDATOR.md` for the canonical two-message row schema,
stable rule trace, output artifacts, and evidence boundary. The serialized-row
validator cannot execute hidden semantic tests because those must remain out of
the row; do not use it to manufacture or replace the private oracle receipt.

When `pre.jsonl` is missing, retain the validator's reconstruction as advisory
analysis only. Never release it, treat it as authoritative provenance, or use
it to claim producer-projection or consumer readiness.

## 4. Categorize and tag every row

Use tags that support balancing, diagnostics, and regression analysis. Include:

- task family and domain;
- target capability;
- output mode and interaction mode;
- algorithm, tool, or reasoning pattern;
- stateful versus stateless behavior;
- edge-case and failure-mode tags;
- difficulty and resource profile;
- source, split, revision, and synthetic status;
- verification status and oracle type;
- safety, privacy, or contamination risk.

Prefer explicit tags such as `mutation-atomicity`, `boundary-conditions`,
`tool-repair`, `deterministic-ordering`, or `calibrated-abstention` over vague
labels such as `hard` or `quality`.

## 5. Detect duplicates and lineage

Compare within the candidate set and against all existing sets at multiple
levels:

1. exact row hash;
2. exact task ID or label;
3. normalized prompt and answer;
4. prompt-only and answer-only matches;
5. revision suffixes and explicit parent metadata;
6. source slug and source hash;
7. template, paraphrase, or semantic overlap;
8. equivalent tests, APIs, or solution contracts under different names.

Classify matches instead of calling all of them duplicates:

| Relation | Default action |
| --- | --- |
| Exact duplicate | Keep one canonical row |
| Same-ID correction | Replace the ancestor after verification |
| Versioned revision | Keep the newest verified version; preserve lineage |
| Paraphrase with identical target | Down-weight or keep one representative |
| Shared concept, distinct contract | Keep if it adds measurable coverage |
| Conflicting answers | Quarantine and adjudicate |
| Collision-qualified variants | Review APIs and tests before keeping both |

Do not train an ancestor and its correction as independent examples unless the
training format explicitly teaches critique and correction.

## 6. Audit contamination and split integrity

Check more than exact task IDs:

- benchmark names and public exercise IDs;
- prompt, title, filename, symbol, and test similarity;
- answer or reference-code similarity;
- shared templates and generated variants;
- parent-child lineage across splits;
- hidden labels, expected outputs, tests, rubrics, or judge feedback;
- near-duplicate domains that preserve the same executable contract.

Use group-aware splits by underlying task, template, source family, and revision
lineage. If a row teaches an evaluation answer directly, remove it from training
or move the evaluation surface.

## 7. Verify correctness with the strongest oracle

Prefer deterministic evidence. Use the strongest applicable method:

| Task type | Preferred evidence |
| --- | --- |
| Code | Build, tests, hidden tests, sanitizers, static checks, complexity probes |
| Math or logic | Exact solver, symbolic check, property tests, counterexamples |
| Extraction | Source-grounded field comparison and span provenance |
| Transformation | Round-trip, invariant, and property-based checks |
| Tool or agent task | Sandboxed replay, final-state assertions, action constraints |
| Structured output | Schema validation plus semantic field checks |
| Open-ended response | Explicit rubric, independent judges, factual grounding |
| Safety behavior | Adversarial cases, policy rubric, false-positive audit |

Run tests answer-blind where possible. A compile pass proves syntax, not semantic
correctness. A reward, confidence score, or judge approval does not override a
deterministic counterexample.

### Use model judges carefully

- Give the judge the task contract and candidate, not the desired verdict.
- Require a verdict, confidence, evidence, and concrete counterexample.
- Use independent judges or adjudication for uncertain and high-impact rows.
- Separate specification ambiguity from answer failure.
- Send disagreements and low-confidence rows to review.
- Never make judge approval the sole hard gate when executable evidence exists.

## 8. Evaluate signal density and teaching value

Apply soft scoring only after hard gates pass. Score each survivor for:

- directness of the desired behavior;
- correctness coverage, including failure behavior;
- clarity and absence of contradictory prose;
- realism of inputs, tools, and state;
- novelty relative to the retained corpus;
- rare capability or failure-mode coverage;
- answer concision and token efficiency;
- difficulty appropriate to the target model;
- usefulness for the declared evaluation and deployment distribution.

Do not reward length, stylistic polish, or exotic difficulty by default.

## 9. Audit corpus composition

Report counts by family, capability, source, difficulty, verification method,
token bucket, and revision status. Detect:

- dominant templates or families;
- repeated easy examples;
- rare but critical behaviors with too little coverage;
- synthetic-source monocultures;
- answer-length and difficulty skew;
- conflicting style or tool contracts;
- distribution mismatch with evaluation and deployment.

Balance by underlying behavior, not merely topic name. Preserve a verified
anchor set and add the smallest tranche that tests the next hypothesis.

For Aider fixed-26 improvement audits, explicitly report fixed-26 analog
coverage, exact and semantic holdout overlap, file-layout mix, single-turn
versus repair-trajectory share, duplicate instruction headers, whole-edit parse
rate, context/token length buckets, starter-to-answer copy ratios, and
per-row compile/test/sanitizer receipt coverage. Compare the selected mixture
against the fixed-26 count targets: minimum 1,000 new benchmark-shaped
rows/tasks, normal 1,500-2,500 new high-quality rows/tasks, failed-family
analogs 920-1,380, second-try-only families 180-300, multi-file API discipline
250-400, repair trajectories 300-500, and filtered current synthetic anchors
300-600. A clean exact-label overlap check is not enough to call the corpus
aligned.

## 10. Assign a row disposition

Give every row one terminal or actionable status:

- `train`: all hard gates pass;
- `replace-ancestor`: verified correction or revision;
- `review`: ambiguity, weak evidence, or unresolved overlap;
- `repair-and-reverify`: deterministic defect with recoverable source evidence;
- `reject`: wrong, leaked, unverifiable, conflicting, or malformed;
- `eval-only`: useful diagnostic that must not enter training.

Do not call a dataset train-ready while selected rows still have unresolved hard
gates.

## 11. Validate with training and held-out execution

Treat dataset audit and model validation as separate evidence tiers:

1. train a bounded canary or short checkpoint sequence;
2. keep model, optimizer, inference, and evaluation contracts fixed;
3. evaluate first-attempt success, repair success, and best-of-N separately;
4. run multiple seeds when sampling is stochastic;
5. report per-task gains, retained tasks, and regressions;
6. measure format validity, tokens, latency, and context exhaustion;
7. promote only on held-out task success, not training loss alone.

## Required outputs

Produce these artifacts or their equivalents:

- immutable source manifest and hashes;
- row-level audit catalog with categories, tags, evidence, and disposition;
- duplicate and revision-lineage report;
- contamination and split audit;
- tokenizer and length audit;
- verification receipt with oracle versions and test outcomes;
- category, tag, source, and token summaries;
- selected train and validation manifests;
- rejected and review queues with reasons;
- train-readiness decision and explicit limitations.

Lead the final report with confirmed counts, unresolved risks, and the next gate.
Keep structural validity, executable correctness, and completed training as
separate claims.

## Non-negotiable failures

Reject or quarantine a row when any of these is true:

- the target answer is known wrong or contradicted by a valid counterexample;
- evaluation labels, hidden tests, or private references leak into the input;
- the row exceeds the actual training context after official tokenization;
- the answer violates the required action or output contract;
- source or revision lineage is unknown where contamination matters;
- an ancestor and correction conflict without an explicit teaching structure;
- a code target lacks current strict build, test, sanitizer, or
  plausible-but-wrong discriminator evidence where those checks apply;
- privacy, licensing, secret, or policy constraints prohibit use.

Do not convert absence of a discovered defect into proof of quality.
