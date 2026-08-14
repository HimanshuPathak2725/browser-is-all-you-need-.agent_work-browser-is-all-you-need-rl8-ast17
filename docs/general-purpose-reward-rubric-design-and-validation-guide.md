# General-purpose reward rubric design and validation guide

## Purpose

This guide explains how to design, implement, test, calibrate, and operate a
reward rubric for machine-learning agents or other automated systems. It is
intended to be reusable across code editing, tool use, structured generation,
repository repair, data transformation, planning, and other tasks with
machine-checkable outcomes.

The central principle is:

> Preserve rich, causal, independently verifiable evidence; reduce it to a
> scalar only at the optimizer boundary.

A good rubric is not merely a list of desirable qualities and weights. It is a
versioned measurement contract linking each attribute to exact evidence,
applicability, failure semantics, anti-gaming controls, receipts, calibration
examples, and release gates.

## What a rubric must and must not do

A rubric should:

- identify behavior the system can actually control;
- distinguish prerequisite failure from downstream consequences;
- reward the intended task outcome rather than an easy proxy;
- remain deterministic or have explicitly measured uncertainty;
- separate model failure from evaluator or infrastructure failure;
- produce enough variation for learning without sacrificing correctness;
- retain evidence needed to explain every score; and
- remain stable and versioned throughout a matched experiment.

A rubric must not:

- leak hidden answers or evaluator internals into the model context;
- turn unavailable evidence into a silent pass;
- let style or verbosity compensate for incorrect behavior;
- map sandbox, network, compiler, or evaluator faults to model penalties;
- use a scalar score as proof of task validity, training admission, or
  promotion; or
- change weights, thresholds, parser behavior, or evidence semantics without a
  new policy identity and new validation.

## Core terminology

| Term | Definition |
| --- | --- |
| Attribute | One behavior or property the rubric intends to measure. |
| Check or kernel | A concrete evaluator that produces evidence for one narrowly defined condition. |
| Outcome | The check result, usually pass/fail or a bounded value. |
| Observed | The evaluator actually reached the condition and obtained valid evidence. |
| Applicable | The condition is meaningful for this task or candidate. |
| Not reached | An upstream prerequisite failed, so the evaluator could not test this condition. |
| Infrastructure fault | Evaluation failed for reasons outside the candidate's behavior. |
| Hard gate | A conjunctive requirement that cannot be offset by weighted credit. |
| Reward | The bounded scalar passed to the optimizer. |
| Diagnostic vector | The complete set of check outcomes and evidence before scalar projection. |
| Receipt | A versioned, digest-bound record sufficient to replay and validate a decision. |
| Calibration set | Known examples spanning correct, partially correct, invalid, unsafe, adversarial, and infrastructure-fault cases. |
| Admission | Authorization for a narrowly declared next stage, not a general quality label. |

## The end-to-end design process

### Step 1: freeze the decision the rubric supports

Write down the exact decision before choosing attributes.

Examples:

- rank eight candidate edits for one prompt;
- block unsafe tool trajectories;
- determine whether a task package is valid;
- decide whether an optimizer update has usable signal;
- select a checkpoint after a matched canary; or
- certify an artifact for a specific consumer.

Do not use one score for all of these. They involve different subjects,
evidence, and error costs.

Record:

```text
subject:
decision:
authorized next action:
false-positive cost:
false-negative cost:
hard-stop conditions:
evidence retention period:
```

### Step 2: define the task and execution contract

Freeze the observable contract:

- valid inputs and their schema;
- exact output format;
- allowed actions and editable scope;
- required public behavior;
- target language, protocol, or runtime version;
- environment and resource limits;
- deterministic versus stochastic components;
- hidden evidence boundaries;
- timeout ownership; and
- what constitutes a complete success.

Many poor rubrics begin with generic attributes such as “quality” or “style”
before the output and execution contract is precise. This makes scoring
ambiguous and hard to test.

### Step 3: build an evidence-backed failure taxonomy

Use real failures from a valid evaluator. Group them by causal mechanism, not
only by visible error text.

Typical families are:

1. unsafe or forbidden action;
2. missing or empty output;
3. schema, delimiter, or parser failure;
4. wrong target, scope, label, or public interface;
5. duplication, collision, or conflicting definitions;
6. static validity or compilation failure;
7. startup, timeout, crash, or state-corruption failure;
8. functional or semantic failure;
9. non-functional failure such as concurrency, resource, or determinism; and
10. evaluator or infrastructure failure.

For every family, record:

- observed symptoms;
- plausible root mechanisms;
- a probe that distinguishes those mechanisms;
- whether the model can control the result;
- whether the failure blocks later evaluation; and
- how a known positive and negative example should score.

Do not create attributes merely because a metric is available. Create them
because evidence shows they correspond to a meaningful, controllable failure
or success mode.

### Step 4: draw the causal evaluation graph

Order checks by reachability. A general executable task might follow:

```text
safety
  -> payload exists
  -> schema parses
  -> scope/API is correct
  -> static validation
  -> build/link
  -> bounded runtime
  -> partial semantics
  -> full semantics
  -> sanitizer/concurrency/determinism
```

The graph determines:

- which checks can be evaluated after each failure;
- which failures are primary causes;
- which results are merely not-reached consequences;
- where hard caps should apply; and
- how much partial progress can be rewarded safely.

Never count a compile failure again as five runtime failures and five hidden
test failures. Preserve those downstream outcomes as `not_reached`, but do not
pretend they are independent observations.

### Step 5: choose exact attributes

An attribute should be admitted only if it meets the following tests.

| Selection criterion | Question |
| --- | --- |
| Relevance | Does the attribute directly support the declared task outcome? |
| Controllability | Can the candidate's behavior change the result? |
| Observability | Can the evaluator obtain objective evidence? |
| Locality | Can failure be attributed to a narrow mechanism? |
| Independence | Does it add information not already supplied by another check? |
| Monotonicity | Is passing genuinely no worse than failing? |
| Stability | Is the result reproducible under the frozen environment? |
| Coverage | Does it apply to enough tasks to matter, or is applicability explicit? |
| Gaming resistance | Can it be passed without achieving the intended behavior? |
| Cost | Is its runtime and storage cost acceptable at the intended frequency? |
| Actionability | Does failure tell the owner what to fix? |
| Versionability | Can its semantics be frozen and replayed? |

Reject, split, or keep as telemetry any attribute that fails these questions.

#### Attribute specification card

Create one card per attribute:

```yaml
id: SEM-03
name: boundary_behavior
purpose: Prove behavior at the declared public boundary.
subject: one candidate in one isolated workspace
prerequisites: [runtime_started, verifier_handshake]
applicability_rule: always
evaluator: private_partition_3
evidence_type: executable_receipt
pass_condition: exit_zero_and_nonce_match
fail_condition: observed_nonzero_candidate_status
not_reached_condition: runtime_prerequisite_failed
infrastructure_condition: runner_or_environment_fault
reward_role: semantic_progress
hard_gate: false
weight_rationale: independent boundary behavior
negative_controls: [off_by_one, empty_input, maximum_input]
owner: verifier-team
policy_version: rubric-v1
```

If this card cannot be completed precisely, the attribute is not ready for the
optimizer.

### Step 6: separate hard gates, reward, and telemetry

Use three distinct classes.

#### Hard gates

Hard gates address conditions that weighted averaging must never override:

- unsafe behavior;
- hidden-data access or evaluator spoofing;
- malformed or tampered receipts;
- infrastructure faults;
- non-finite arithmetic;
- train/evaluation contamination;
- wrong task-group identity;
- missing required evidence; and
- unauthorized lifecycle transition.

#### Optimizer reward

Reward should represent bounded, candidate-controlled progress toward the task
outcome. Examples include parse validity, API correctness, compilation,
runtime reachability, and independent semantic partitions.

#### Telemetry

Telemetry is useful for diagnosis but not yet safe as reward:

- output length;
- execution duration;
- style and formatting quality beyond the public contract;
- token entropy and repetition;
- AST size or edit size;
- hidden-state or attention drift;
- memory use within an already valid bound; and
- natural-language judge explanations.

Move telemetry into reward only after a matched experiment proves calibration,
monotonicity, incremental value, and resistance to gaming.

### Step 7: define observation and applicability explicitly

Every check should record both `observed` and `applicable`.

| State | Outcome handling |
| --- | --- |
| Observed and applicable | Use the check's real result. |
| Not observed because prerequisite failed | Record diagnostic failure/not-reached evidence; exclude from independent optimizer credit. |
| Not applicable by task contract | Exclude from the denominator and record why. |
| Infrastructure failure | Mask the sample and fail/abort the relevant batch. |
| Missing evidence | Fail closed as a receipt or admission error. |

Do not encode “not applicable” as a free success. Do not encode infrastructure
failure as candidate failure. Do not erase not-reached checks from the receipt.

### Step 8: choose the scalar projection

There is no universally correct formula. Select the simplest projection that
preserves the task's causal structure.

#### Suitable patterns

**Hard-gated weighted score**

Use when most attributes are independently observable:

```text
R = hard_gate * sum(w_i * s_i)
```

**Reachability plus semantic score**

Use when evaluation is staged:

```text
R = alpha * diagnostic_score
  + beta  * deepest_verified_stage
  + gamma * independent_semantic_fraction
```

**Lexicographic decision**

Use for admission or promotion where no tradeoff is permitted:

```text
all critical rules pass
AND all required evidence exists
AND weighted summary >= threshold
```

The weighted summary is additional evidence. It cannot override a failed hard
rule.

#### Monotonicity requirements

Prove at least:

- a complete valid solution receives the maximum;
- an unsafe solution receives the minimum or no trainable reward;
- correcting one independent failed check cannot lower reward;
- a compile failure cannot outrank a semantically correct executable result;
- a style-only improvement cannot overcome a semantic regression;
- a not-applicable check cannot create free reward;
- an infrastructure fault cannot create a model penalty; and
- every cap and override is deterministic.

### Step 9: choose weights with evidence

Weights express marginal decision importance, not how many metrics happen to
exist in a category.

Use this procedure:

1. Rank failure families by task impact and irreversibility.
2. Identify hard gates before assigning any weights.
3. Remove redundant checks or group them into one tier.
4. Allocate most semantic mass to independently executable correctness.
5. Give prerequisite format/static checks enough mass to create learning
   signal, but not enough to outrank functional success.
6. Normalize weights to a documented total.
7. Compute the reward change caused by every one-check flip.
8. Perform sensitivity analysis on representative and adversarial candidates.
9. Verify rank order against manual judgments and executable ground truth.
10. Freeze the vector as a new policy version.

#### Weight-calibration table

| Candidate type | Required relative order |
| --- | --- |
| Unsafe or evaluator-spoofing | Lowest or masked |
| Empty/unusable output | Below substantive malformed output |
| Parseable but wrong scope | Below correct-scope static failure |
| Static-valid but non-linking | Below executable candidate |
| Executable with no semantic passes | Below partial semantic pass |
| Partial semantic success | Below complete semantic success |
| Complete success with valid safety evidence | Maximum |

If reasonable weight perturbations reverse these fundamental rankings, the
rubric is too fragile.

### Step 10: choose thresholds through calibration

Never copy threshold values from unrelated papers or projects without a matched
baseline.

Build a calibration set containing:

- known full successes;
- known safe partial successes;
- failures at each causal stage;
- no-op and empty outputs;
- unsafe and adversarial outputs;
- reward-hacking attempts;
- not-applicable cases;
- evaluator tampering; and
- injected infrastructure faults.

For each threshold:

1. define the metric exactly, including denominator and missing-data behavior;
2. measure the current baseline distribution;
3. measure verified positive and negative anchors;
4. select a boundary tied to the operational decision and error cost;
5. validate it on a task-disjoint holdout;
6. run sensitivity analysis around the boundary;
7. require confidence intervals for stochastic metrics;
8. freeze the value, sample size, aggregation, and failure action; and
9. change it only through a new versioned experiment.

Distinguish:

- per-candidate thresholds;
- per-group signal thresholds;
- per-batch infrastructure thresholds;
- checkpoint stop thresholds; and
- promotion thresholds.

A 50% batch format floor, for example, does not mean a malformed individual
response should be treated as infrastructure failure.

### Step 11: design exact receipts

A replayable receipt should include:

```json
{
  "schema_version": "reward-receipt-v1",
  "policy_version": "rubric-v1",
  "subject_id": "task-and-candidate-id",
  "task_sha256": "...",
  "prompt_sha256": "...",
  "starter_sha256": "...",
  "response_sha256": "...",
  "evaluator_sha256": "...",
  "environment_digest": "sha256:...",
  "checks": {},
  "observed": {},
  "applicable": {},
  "evidence": {},
  "primary_failure": "...",
  "not_reached": [],
  "infrastructure_error": false,
  "component_scores": {},
  "pre_override_score": 0.0,
  "override": "none",
  "optimizer_score": 0.0,
  "private_details_disclosed": false
}
```

Validation must reject:

- missing or extra required keys;
- wrong check identities;
- Boolean values accepted where strict integers are required;
- zero, NaN, infinity, or out-of-range values;
- arithmetic disagreement;
- an impossible stage/check combination;
- a pass without evidence;
- a result whose subject hashes do not match; and
- receipts manually edited after production.

Store private details separately from model-facing logs. Aggregated monitoring
must not expose hidden answers, paths, test names, or expected values.

### Step 12: isolate model context from evaluator context

The model should see only the public task, allowed inputs, and explicitly
authorized feedback. It should not see:

- rubric names, IDs, weights, or score values;
- hidden tests, references, expected outputs, or partition labels;
- failure-frequency hints from other tasks;
- another candidate's response or feedback;
- optimizer losses, advantages, KL, gradients, or checkpoint decisions;
- absolute evaluator paths, secrets, nonces, or markers; or
- benchmark evaluation material reserved for post-training measurement.

Require exact prompt hashes, one prompt identity per relative-reward group,
fresh candidate state, independent workspaces, and no automatic recycling of
private traces into future prompts.

### Step 13: freeze lifecycle and claim boundaries

Maintain separate statuses for:

```text
task_validation
reward_validation
dataset_validation
curriculum_validation
training_admission
optimizer_canary
training_dynamics
external_evaluation
checkpoint_promotion
consumer_verification
deployment_certification
```

Every PASS must state its exact subject hash and authorized next action. A later
stage reruns or verifies every earlier dependency. Any change to the task,
oracle, evaluator, parser, policy, tokenizer, prompt, model, dataset, or
environment invalidates dependent receipts.

## Complete test program

### A. Schema and arithmetic tests

Test:

- all-minimum and all-maximum vectors;
- every tier/check milestone;
- exact weight sum;
- every reachability stage;
- every semantic fraction;
- one-check flips;
- caps and overrides;
- finite range at every intermediate step;
- missing, extra, duplicate, wrong-type, zero, NaN, and infinite fields;
- serialization/deserialization round trips; and
- backward compatibility for intentionally supported prior versions.

Use exact rational or decimal arithmetic where floating-point ambiguity would
change a boundary decision.

### B. Causal and reachability tests

For each stage, create a candidate that fails exactly there. Verify:

- the primary cause is correct;
- later checks are marked not reached;
- earlier successful evidence is retained;
- the scalar is inside the intended interval;
- fixing only that defect advances the stage monotonically; and
- consequence checks do not create duplicate penalties.

### C. Parser and format tests

Cover:

- empty output;
- whitespace/comments only;
- missing, extra, nested, or unclosed delimiters;
- encoding errors and NUL bytes;
- exact versus recovered labels;
- duplicate and case-folded paths;
- path traversal and absolute paths;
- extra prose or undeclared payloads;
- terminal-token normalization; and
- maximum byte and token boundaries.

Parser recovery rules must be explicit. A recovered output should not silently
receive the same format evidence as an exact output.

### D. Static and interface tests

Use isolated probes for:

- exact names and case;
- namespaces and module/package ownership;
- signatures, overloads, templates, generics, qualifiers, and exceptions;
- header or schema self-containment;
- undeclared dependencies;
- warnings-as-errors;
- duplicate definitions;
- editable/protected scope; and
- expected artifact production.

Prefer AST/schema-aware evidence over regular-expression presence when exact
public structure matters.

### E. Executable semantic tests

Require:

- build/link evidence;
- bounded startup and termination;
- independent semantic partitions;
- boundary and adversarial inputs;
- state-transition and invariant checks;
- repeated deterministic execution;
- resource-limit behavior;
- memory/undefined-behavior tooling where applicable;
- concurrency/race tooling where applicable; and
- a full-suite consistency run.

Hidden partitions should be nonempty, deterministic, disjoint, balanced by
behavioral mechanism, and receipt-bound. Their union should reconcile with the
declared full semantic contract.

### F. Sandbox and anti-cheat tests

Attempt at least:

- path traversal and symlink escape;
- protected-file reads or writes;
- process spawning and shell execution;
- network access;
- privilege/capability manipulation;
- environment or secret probing;
- output-marker and receipt spoofing;
- dynamic loading or symbol interposition;
- exit, signal, macro, or linker interception;
- static-initializer bypasses;
- excessive process, file, memory, or time consumption; and
- workspace mutation outside declared scope.

Use unpredictable per-run handshakes and before/after workspace snapshots.

### G. Infrastructure fault-injection tests

Deliberately inject:

- missing compiler/runtime;
- invalid evaluator image;
- unavailable sanitizer;
- outer watchdog termination;
- disk-full or read-only scratch failure;
- corrupted receipt storage;
- worker loss;
- malformed hidden artifact; and
- clock or nonce-service failure.

Verify every case is classified as infrastructure failure, the optimizer update
is blocked, and no candidate receives a negative reward for it.

### H. Reward-ranking and anti-hacking tests

Create anchor candidates with known order:

- full verified success;
- partial semantic success;
- executable semantic failure;
- link failure;
- static failure;
- parse failure;
- empty/no-op output;
- unsafe bypass attempt; and
- evaluator spoofing attempt.

Add adversarial pairs that improve a proxy while worsening the task:

- better style but wrong output;
- shorter response but incomplete work;
- faster runtime by skipping required behavior;
- hard-coded visible cases;
- duplicated definitions that satisfy a text search;
- fake success markers;
- deletion of difficult tests or configuration; and
- intentional first-turn failure to earn a repair bonus.

The rubric must preserve the intended order and reject compensation attacks.

### I. Context isolation and leakage tests

Verify:

- exactly the allowed message count and order;
- byte-identical initial prompts within a relative-reward group;
- no message, output, or feedback from another candidate;
- fresh workspace and state per candidate;
- no reward or rubric text in prompts;
- no private markers, paths, expected values, or test names;
- no external benchmark material in training;
- exact tokenizer/template replay;
- zero silent prompt truncation;
- candidate-local and bounded repair feedback; and
- no replay-buffer auto-ingestion of raw private artifacts.

Use exact and normalized contamination scans. Semantic-review findings should
fail closed until adjudicated.

### J. Group and batch signal tests

Before each optimizer update, verify:

- expected group count and sample count;
- one logical task and prompt per group;
- unique logical tasks across batch slots when required;
- independent sample seeds, responses, and workspaces;
- exact complete receipts;
- zero infrastructure faults and non-finite values;
- sufficient positive semantic groups;
- sufficient semantic, reward, and diagnostic-vector variance;
- frozen format and execution reachability rates;
- no train/monitor overlap; and
- token limits and context-isolation receipts.

Apply these gates on **every** optimizer update. The existence of an earlier
PASS receipt must never disable current validation.

### K. Optimizer numerical tests

Test with synthetic groups:

- identical rewards;
- very small reward variance;
- one extreme reward;
- mixed positive and negative rewards;
- all minimum and all maximum rewards;
- invalid/masked samples; and
- groups from different tasks.

Prove:

- advantages are computed only within the exact task/prompt group;
- homogeneous groups produce exactly zero policy-gradient contribution;
- non-finite rewards, advantages, ratios, KL, losses, and gradients stop the
  update;
- clipping and KL fields have exact documented definitions;
- gradient norm limits are enforced;
- cross-task reward normalization is impossible; and
- masked infrastructure samples cannot influence baselines.

An epsilon denominator prevents division by zero, but does not by itself prove
correct credit assignment.

### L. Determinism, portability, and performance tests

Measure:

- repeated reward equality on identical bytes;
- stable partition results;
- compiler/runtime portability where part of the contract;
- timeout boundaries and inner/outer ownership;
- peak memory and disk use;
- verifier throughput and queue behavior;
- rollout length and truncation;
- checkpoint publication atomicity; and
- receipt/manifests after process interruption and resume.

Performance optimization must not weaken isolation, hidden evidence, or
determinism.

### M. Canary, evaluation, and promotion tests

Use a small, explicitly authorized canary before full training. Freeze:

- control checkpoint;
- task and monitoring partitions;
- model, adapter, tokenizer, template, prompt, and environment;
- reward and optimizer policy;
- seeds or seed policy;
- checkpoint interval and selection rule;
- stop conditions; and
- number of matched trials.

Log task-correctness metrics at every checkpoint, not only loss. Compare
fail-to-pass, pass-to-fail, stable-pass, and stable-fail transitions. Use an
unseen shadow set and confidence intervals. Promotion should require strict
task improvement plus bounded regressions and all hard gates.

External benchmark suites should remain evaluation-only and task-disjoint from
training, repair, monitoring prompts, and replay buffers.

## How to decide whether a metric becomes reward

Use the following decision table.

| Question | If no |
| --- | --- |
| Is the metric directly linked to public task success? | Keep as telemetry. |
| Can the candidate control it? | Treat as environment/evaluator evidence. |
| Is it deterministic or calibrated? | Keep as research telemetry. |
| Does it add information beyond existing checks? | Remove or merge it. |
| Is its applicability explicit? | Do not use it. |
| Is it monotonic with quality? | Do not reward it. |
| Can obvious proxy attacks be rejected? | Do not reward it. |
| Is the evaluator isolated from the model? | Fix leakage before use. |
| Are positive/negative anchors and thresholds validated? | Do not gate on it. |
| Can its arithmetic and evidence be replayed? | Do not send it to the optimizer. |

## Common mistakes to avoid

### Rubric-design mistakes

- Using vague categories such as “quality” without a concrete evaluator.
- Giving each available metric a weight, even when metrics overlap.
- Rewarding style, brevity, or speed before correctness.
- Double-charging one upstream failure through every later stage.
- Globally renormalizing weights so missing evidence changes reward identity.
- Treating not-applicable as a free pass.
- Treating not-reached as independently observed failure.
- Allowing a weighted total to override safety or contamination.
- Adding a repair bonus that incentivizes intentional initial failure.
- Changing weights during training without a new policy version.

### Evaluation mistakes

- Using regex presence when exact structural/API evidence is required.
- Counting compile-blocked attempts as semantic failures.
- Stopping hidden evaluation at the first failure when partial signal matters.
- Reporting a union across candidates as individual pass@k.
- Using only aggregate reward without kernel/stage distributions.
- Inferring entropy from sampled-token log probabilities alone.
- Comparing KL fields that use different estimators or references.
- Setting numerical thresholds from unrelated literature without calibration.
- Ignoring duplicate logical tasks in a relative-reward batch.
- Running signal gates only on the first update.

### Security and privacy mistakes

- Exposing rubric weights or hidden-test hints to the model.
- Returning private compiler/test output as repair feedback.
- Reusing another candidate's response, context, or workspace.
- Training on evaluation benchmark prompts or task-level failure artifacts.
- Storing private receipts in model-facing datasets.
- Accepting self-reported success markers without an unpredictable handshake.
- Letting the candidate modify tests, graders, build files, or receipts.

### Experiment and lifecycle mistakes

- Launching full training after only local unit tests.
- Treating one short run as statistically meaningful improvement.
- Selecting the final checkpoint automatically instead of a frozen policy.
- Using low training loss as promotion evidence.
- Comparing unmatched harnesses, prompts, seeds, or feedback policies.
- Recording only a Git commit while executing uncommitted source bytes.
- Manually editing generated receipts or PASS reports.
- Conflating task validation, training admission, checkpoint promotion, and
  deployment certification.

## Minimum reusable artifacts

Every production rubric project should maintain:

1. a versioned rubric specification;
2. an exact attribute registry and causal graph;
3. a schema for candidate receipts;
4. positive, partial, negative, adversarial, and infrastructure controls;
5. deterministic unit and integration tests;
6. a calibration and threshold report;
7. a context-isolation and leakage report;
8. a sandbox/security report;
9. a batch signal-gate receipt;
10. a canary plan and matched control ledger;
11. checkpoint dynamics and selection records;
12. an external evaluation report; and
13. separate admission, promotion, consumer, and deployment decisions.

## Rubric review worksheet

Use this checklist before the first optimizer step.

### Contract

- [ ] The task, output, action, runtime, and success contracts are exact.
- [ ] The rubric subject and authorized decision are explicit.
- [ ] The threat model and private evidence boundary are documented.
- [ ] All identities and environments are digest-bound.

### Attributes

- [ ] Every attribute is relevant, controllable, observable, and actionable.
- [ ] Redundant attributes are removed or grouped.
- [ ] Prerequisites, applicability, and not-reached semantics are explicit.
- [ ] Hard gates, optimizer reward, and telemetry are separate.
- [ ] Every attribute has positive, negative, and adversarial controls.

### Scoring

- [ ] The formula, weight total, range, caps, and overrides are exact.
- [ ] All-minimum, all-maximum, milestone, and one-flip tests pass.
- [ ] Fundamental candidate ranking is stable under sensitivity analysis.
- [ ] Infrastructure faults produce no model reward.
- [ ] Missing/non-finite/tampered evidence fails closed.

### Isolation

- [ ] Prompts contain no rubric, hidden, reference, or benchmark material.
- [ ] Relative-reward groups use one exact prompt and task.
- [ ] Candidate messages, workspaces, outputs, and feedback are independent.
- [ ] Prompt/token boundaries replay with zero silent truncation.
- [ ] Private raw artifacts cannot enter training automatically.

### Optimizer gate

- [ ] Group and sample counts are exact.
- [ ] Logical task uniqueness is enforced where required.
- [ ] Positive and variance requirements are calibrated and pass.
- [ ] Homogeneous groups have proved zero-gradient behavior.
- [ ] Reward, advantage, ratio, KL, loss, and gradient values are finite.
- [ ] The complete gate executes before every optimizer update.

### Lifecycle

- [ ] A no-update canary passes.
- [ ] A bounded optimizer canary is explicitly authorized.
- [ ] Checkpoint metrics include task correctness, not only training loss.
- [ ] Matched trials and an unseen shadow set are frozen.
- [ ] Promotion and deployment remain separate decisions.
- [ ] Any missing evidence is reported as `not_completed`.

## Final rule

The safest general pattern is:

```text
public task contract
  -> isolated candidate
  -> private causal diagnostic vector
  -> exact receipt validation
  -> per-update signal gate
  -> bounded scalar reward
  -> quarantined checkpoint
  -> matched canary and shadow evaluation
  -> separate promotion decision
  -> separate deployment decision
```

When uncertain, retain the measurement as telemetry, collect calibration
evidence, and postpone using it as reward. It is easier to add a proven signal
in a new policy version than to undo training driven by a leaky or gameable
proxy.
