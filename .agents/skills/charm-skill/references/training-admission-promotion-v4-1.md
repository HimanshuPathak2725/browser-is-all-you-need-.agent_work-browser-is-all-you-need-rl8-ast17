# CHARM V4.1 Training Admission, Promotion, and Deployment

Read this reference with `generator-admission-v4.md`. V4.1 is a cumulative,
fail-closed overlay. It does not weaken task, oracle, security, Baseline-3,
Validator V2, serialization, or repository-wide uniqueness requirements.

## Contents

- [Decision boundaries](#decision-boundaries)
- [End-to-end state machine](#end-to-end-state-machine)
- [Training admission gates](#training-admission-gates)
- [Repair and calibration curriculum](#repair-and-calibration-curriculum)
- [Dataset shape and API prediction](#dataset-shape-and-api-prediction)
- [Canary and training dynamics](#canary-and-training-dynamics)
- [Checkpoint promotion](#checkpoint-promotion)
- [Promotion score](#promotion-score)
- [Strengthened baselines](#strengthened-baselines)
- [Deployment certification](#deployment-certification)
- [Manual review sequence](#manual-review-sequence)
- [Claim boundaries](#claim-boundaries)

## Decision boundaries

V4.1 separates six questions that must not be collapsed:

| Decision | Question | Hard-pass output |
| --- | --- | --- |
| Task validation | Is each exact task safe, solvable, executable, and unique? | Per-task proof receipt |
| Dataset validation | Do exact serialized rows reconcile with exact tasks? | Corpus receipt |
| Curriculum validation | Does the mixture teach the required actions, repairs, and calibration? | Curriculum receipt |
| Training admission | Is a bounded canary justified before any optimizer step? | Pre-training PASS |
| Checkpoint promotion | Did matched held-out and shadow evaluation improve? | Promotion PASS |
| Deployment certification | Is the promoted artifact operationally ready? | Deployment PASS |

A later decision reruns every earlier decision. Missing evidence is
`not_completed`, never PASS. A weighted score cannot override a failed hard
rule.

## End-to-end state machine

```text
valid post-run evidence + previous-best attempt ledger
  -> failure-conditioned synthesis authorization
  -> freeze task count, roles, starters, layouts, API capabilities
  -> freeze repair, calibration, header-mode, shape, exposure, and canary plans
  -> repository-wide uniqueness PASS before generation
  -> pre-generation V4.1 PASS
  -> generate through owner-controlled sources
  -> API/oracle/grader/safety/application proof for every task
  -> repository-wide uniqueness PASS after generation
  -> post-generation V4.1 PASS
  -> independent read-only audit
  -> owner repair, regeneration, and fresh proof loop
  -> exact private projection and production serialization replay
  -> complete dataset, curriculum, baseline, shape, and API-predictor evidence
  -> pre-training V4.1 PASS
  -> exactly 20-task, 5-epoch canary
  -> log train loss, validation loss, compile rate, hidden-test rate per checkpoint
  -> early stop and choose best 40/40/20 composite checkpoint
  -> matched previous-checkpoint and unseen shadow evaluation
  -> promotion V4.1 PASS
  -> consumer, security, rollback, monitoring, and reproducibility evidence
  -> deployment V4.1 PASS
```

## Training admission gates

### ADM-001 editable-file layout

Freeze counts before generation and derive them again from generated receipts.

| Layout | Admission target |
| --- | ---: |
| CPP only | at most 40% |
| Header only | 10-20% |
| Header and CPP | at least 40% |
| More than two editable files | at least 10% |

The critical outer limits remain CPP-only at most 60%, any header edit at least
10%, and header-plus-CPP at least 30%. V4.1 uses the stricter admission targets
as hard gates for the active remediation profile.

### ADM-002 API capability coverage

Every plan and materialized corpus must contain at least 15 tasks for each
capability. Tags may overlap only when exact task evidence proves both
behaviors.

- implement a missing API;
- preserve an existing API;
- extend an API;
- repair a broken API; and
- refactor while preserving the API.

### ADM-003 starter distribution

| Starter type | Target |
| --- | ---: |
| Empty | 20% |
| Skeleton | 25% |
| Partial implementation | 20% |
| Semantic bug | 15% |
| Compile bug | 10% |
| Near-correct | 10% |

An absolute deviation over five percentage points blocks admission. A deviation
over ten percentage points is critical. Counts must sum to the authorized task
count.

### ADM-004 content-derived reconciliation

At post-generation, recompute role, action topology, editable layout, starter
type, header mode, API capabilities, and repair subtype counts from exact task
receipts. Every recomputed count must equal the frozen plan.

## Repair and calibration curriculum

### CURR-101 repair ratio

Genuine repair trajectories must be 20-30% of the dataset. Below 15% is always
critical; the active V4.1 admission policy enforces the full 20% floor.

### CURR-102 repair subtype coverage

At least 5% of repair rows must cover each subtype:

- compile repair;
- linker repair;
- API repair;
- hidden-test repair;
- runtime repair; and
- sanitizer repair.

One trajectory may carry multiple subtype tags only when the failing receipt
proves each tagged mechanism.

### CURR-103 feedback safety

Repair feedback must be produced by the bound redaction policy, contain at most
100 lines, and disclose none of:

- hidden answers;
- expected outputs;
- private test names or paths;
- assertion bodies; or
- hidden case structure.

Training and promotion use the same redacted lane. Full private output remains
in a separately labeled internal diagnostic lane.

### CAL-001 calibration

Calibration rows are 5-8% of the corpus. Every such receipt has
`task_type=calibration` and an oracle-backed already-correct, no-change,
clarification, or scope-preservation decision.

### HDR-001 header-mode balance

The five modes `frozen`, `editable`, `reconstructed`, `repaired`, and
`extended` must each occupy 10-30% of the authorized plan. The nominal target
is 20% each.

## Dataset shape and API prediction

### SHAPE-001 and SHAPE-002

Both the frozen plan and actual selected corpus contain non-empty histograms
for topic, difficulty, starter, repair, file count, header edits, templates,
exceptions, concurrency, pointers, AST nodes, and API shape. Every family must
meet its predeclared minimum. The actual receipt is digest-bound.

### API-PRED-001

Before training, run a frozen deterministic API reconstruction predictor across
every selected row.

```text
api_reconstruction_score >= 0.97
predicted_api_failure_risk <= 0.03
task_count == selected task count
method and result receipts are SHA-256 bound
```

The predictor supplements executable proof; it never replaces compilation or
the public-API probe.

## Canary and training dynamics

### CAN-001

The current hard canary is exactly 20 tasks and 5 epochs. Full training remains
blocked until it passes. Use at least four frozen matched trials and log
non-zero evaluation rows.

Automatic stop conditions remain:

- mean Pass@1 drop greater than one task;
- public-API absence increase greater than two percentage points;
- any contamination;
- any missing required action topology;
- any malformed output or infrastructure failure; or
- context exhaustion above 1%.

### DYN-001 through DYN-004

DYN-001 freezes complete per-checkpoint logging, DYN-002 requires early
stopping and forbids always-final selection, DYN-003 fixes the selection
weights, and DYN-004 verifies the resulting checkpoint receipt.

Before training, freeze a policy that logs at every checkpoint:

- training loss;
- validation loss;
- compile rate; and
- hidden-test pass rate.

Enable early stopping. Do not use an `always_final` selection policy. Select
the best checkpoint with:

```text
40% compile rate
40% hidden-test pass rate
20% validation-loss component
```

The promotion receipt must contain every checkpoint record and identify the
selected checkpoint and its best-composite reason.

### EXP-001

Observed anchor effective exposure must exactly equal the frozen plan.
Tolerance is zero. Any change in repetitions, epochs, or sampling weight is
curriculum drift and invalidates promotion.

## Checkpoint promotion

The following are conjunctive hard gates:

| Rule | Metric | Threshold |
| --- | --- | ---: |
| PROM-001 | Compile rate | at least 98% |
| PROM-002 | Link rate | at least 98% |
| PROM-003 | Public API exposure | at least 97% |
| PROM-004 | Semantic failure rate | at most 5% |
| PROM-005 | Runtime failure rate | at most 1% |
| PROM-006 | Header reconstruction | at least 95% |
| PROM-007 | Mean Pass@1 | strictly improves previous checkpoint |
| PROM-008 | Evaluation rows | greater than zero |
| PROM-009 | Unseen shadow validation | PASS; compile at least 98%; hidden tests at least 90% |

Promotion also requires evaluator health, a matched previous-best ledger,
complete transition matrix, unchanged redacted-feedback policy, no regression
budget violation, and a digest-bound result.

## Promotion score

`SCORE-001` recomputes:

| Component | Weight |
| --- | ---: |
| Task quality | 15% |
| Curriculum | 20% |
| Admission | 20% |
| Shadow validation | 20% |
| Benchmark simulation | 15% |
| Training dynamics | 10% |

The score must be at least 95/100 and the exact weights must match. It is an
additional threshold. A 100/100 score cannot override even one failed critical
rule.

## Strengthened baselines

### Baseline 1: structural

JSON, metadata, compile evidence, and receipts score at least 90.

### Baseline 2: curriculum

Repair, starter, capability, API, and AST diversity score at least 95.

### Baseline 3: deployment

All conditions are mandatory:

- critical-rule pass fraction exactly 100%;
- major-rule pass fraction at least 98%;
- minor-rule pass fraction at least 95%;
- shadow compile rate at least 98%;
- shadow hidden-test pass rate at least 90%;
- API reconstruction at least 97%;
- header reconstruction at least 95%;
- repair coverage at least 20%;
- calibration coverage at least 5%;
- duplicate risk below 2%;
- generalization risk score at most 0.30;
- candidate Pass@1 improves on the previous checkpoint;
- curriculum drift count is zero; and
- evaluation rows are non-zero.

The original V1 Baseline 3 remains required. This V4.1 definition is a stricter
admission and deployment overlay, not a reinterpretation of an old receipt.

## Deployment certification

`DEP-001` runs only after promotion. It requires digest-bound proof of:

- verified promotion receipt;
- downstream consumer verification;
- complete artifact manifest;
- complete model card;
- rollback plan;
- monitoring plan;
- security review; and
- reproducibility.

The local receipt authorizes only the declared deployment transition. It does
not claim an organizational signature or external certification.

## Manual review sequence

Before generation:

- verify exact failure artifacts and the operator-supplied audit-skill tree;
- inspect the previous-best attempt ledger;
- recompute all planned percentages;
- review API capability, repair subtype, header-mode, and shape plans;
- inspect the repository-wide uniqueness scope and zero-match receipt;
- verify exact source, tokenizer, template, feedback, and canary bindings; and
- run `--stage pre-generation`.

Before training:

- inspect every task proof and post-generation uniqueness result;
- inspect independent-audit findings and owner remediation;
- replay exact serialized rows;
- recompute materialized composition;
- inspect Baselines 1-3, shape, API predictor, duplicate and risk reports; and
- run `--stage pre-training`.

Before promotion:

- inspect the 20-task/5-epoch canary;
- inspect every checkpoint log and the selection calculation;
- compare planned and observed anchor exposure exactly;
- inspect matched and shadow evaluations;
- recompute PROM-001..009 and the 95-point score; and
- run `--stage promotion`.

Before deployment:

- independently verify the promotion receipt;
- inspect consumer, artifact, rollback, monitoring, security, and reproducibility evidence;
- run `--stage deployment`; and
- preserve the immutable deployment bundle.

## Claim boundaries

V4.1 validates evidence supplied in the admission bundle and exact bound files.
It does not train a model, infer missing evaluation rows, sign organizational
certificates, or turn heuristic analytics into deterministic proof. Missing or
unbound evidence fails closed.
