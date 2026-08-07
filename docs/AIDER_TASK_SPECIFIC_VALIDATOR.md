# Aider task-specific validator

This validator is a fail-closed layer after the complete 51-row CHARM V1
Baseline-3 validator. It does not replace Baseline 3 or the full-corpus generic
Validator V2.

```text
exact 51-row Baseline-3 PASS
  -> select only profile-covered topics
  -> validate task/rubric/API/proof/SFT lineage
  -> validate topic-specific prompt and private-test mechanism coverage
  -> rerun strict C++17 and ASan/UBSan in the pinned offline image
  -> emit task-specific PASS receipt
  -> optionally project a receipt-bound SFT slice
```

## Initial scope

The version-1 catalog covers three tasks in each of:

- Clock
- Complex Numbers
- Spiral Matrix
- Zebra Puzzle

The catalog lives at
`configs/aider_task_validator/task-specific-v1.json`. To scale the validator,
add a topic object and one category profile per expected task. No Python branch
is needed for a new topic. Every category profile freezes the slot, role,
editable layout, required tags, public-contract mechanism text, private-test
mechanism evidence, and minimum assertion count.

## Hard gates

Each selected task must pass:

- `TSV2-ID-001`: selected-manifest, released-root, tree, rubric, prompt, and
  hidden-test digest identity;
- `TSV2-ACT-001`: slot, role, layout, source revision, and required tags;
- `TSV2-API-001`: public API equality and declaration visibility;
- `TSV2-MECH-001`: topic/category mechanism is explicit in the public task;
- `TSV2-TEST-001`: certified private tests exercise the declared mechanism;
- `TSV2-ORC-001`: pinned-image oracle matrix, C++17/C++20 repetitions, and
  all deterministic rules pass;
- `TSV2-NEG-001`: starter/failure controls and a compiling semantic mutation
  are rejected by the hidden partition;
- `TSV2-SFT-001`: private/final row reconciliation, message masks, whole-file
  application, and leakage checks;
- `TSV2-EXEC-001`: fresh strict C++17 and ASan/UBSan execution pass.

Private compiler or test output is never stored in the task-specific report.
The report records only return codes, a failure class, and a diagnostic digest.

## Commands

Verify the profile catalog:

```bash
aider-task-specific-validator verify-profiles \
  --profiles configs/aider_task_validator/task-specific-v1.json
```

Run the post-Baseline validator:

```bash
aider-task-specific-validator validate path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --baseline3-summary path/to/dataset_summary.json \
  --selected-manifest path/to/selected_manifest.json \
  --profiles configs/aider_task_validator/task-specific-v1.json \
  --topic Clock \
  --topic "Complex Numbers" \
  --topic "Spiral Matrix" \
  --topic "Zebra Puzzle" \
  --out path/to/immutable-report
```

Project a passing selection without re-rendering or modifying any row:

```bash
aider-task-specific-validator project-slice path/to/train.jsonl \
  --pre-jsonl path/to/pre.jsonl \
  --task-specific-receipt path/to/task-specific-receipt.json \
  --consumer-receipt path/to/consumer_verification.json \
  --out path/to/immutable-slice
```

The slice stores private provenance at `private/pre.jsonl`, model-facing data
at `sft/train.jsonl`, and its bindings in `slice-manifest.json`.

## Claim boundary

A passing slice is `consumer_verified_task_specific_slice` and
`sft_format_ready`. It is not a new full-corpus admission, does not authorize a
training run, and does not claim benchmark uplift, canary success, checkpoint
promotion, or deployment readiness.
