# Aider Shadow-Task Oracle Certification

## Scope

Oracle certification is the mandatory Stage 0 admission gate for the private
Aider C++ shadow corpus. It proves task solvability with a canonical reference
before any task can be materialized into GRPO data. It does not replace later
grader-quality, adversarial-security, reward-density, or curriculum audits.

## Source layout

Every source exercise must contain:

```text
<exercise>/
  .docs/instructions.md
  .reference/<every editable file>   # private canonical solution
  .rubric.json
  CMakeLists.txt
  <starter editable files>
  <slug>_test.cpp                    # private hidden grader
```

The `.reference` directory must be real and non-symlinked. Its file set must
exactly equal `editable_files`; nested paths and extra files are rejected.
References exist only in the private schema-v2 source archive. They are never
copied into `shadow/<exercise>`, task descriptors, prompts, or training JSONL.

The source manifest must declare:

```json
{
  "schema_version": 2,
  "contract": {
    "official_task_id_overlap": [],
    "oracle_references_packaged": true,
    "reference_answers_model_facing": false
  }
}
```

Each schema-v2 rubric declares `reference_answer_packaged: true` and
`reference_answer_model_facing: false`. Generated dataset manifests use schema
version 6 and continue to declare `split_contract.reference_answers_packaged:
false`.

## Certification matrix

For each of all 253 tasks, the validator:

1. Loads the exact private reference files and renders an Aider whole-file
   response.
2. Creates an isolated temporary task containing only starter files and the
   SHA-256-bound hidden grader.
3. Executes the complete Weighted45 policy three times with C++17 and three
   times with C++20.
4. Uses `-O2 -Wall -Wextra -Werror -pedantic`; normal rollout compilation is
   unchanged unless oracle options are explicitly selected.
5. Requires all 45 checks, ASan/UBSan/leak checks, applicable TSan checks, all
   hidden partitions, and the dynamic verifier handshake to pass on every run.
6. Requires every normalized reward to equal exactly `1.000000` and repeated
   outcome signatures to be identical within each language standard.

One rejected task prevents dataset materialization. The builder writes a
`<output>.oracle-rejected/report.json` report before raising. Successful builds
store the aggregate report at `validation/oracle/report.json` and all per-task
receipts under `validation/oracle/receipts/`.

## Stable rules

| Rule | Requirement |
|---|---|
| `ORC-001` | Real, non-symlink `.reference` directory exists |
| `ORC-002` | Reference file set exactly equals `editable_files` |
| `ORC-003` | Reference files are regular direct children |
| `ORC-004` | Reference parses as an exact whole-file response |
| `ORC-005` | Executed hidden grader matches the task SHA-256 |
| `ORC-010` | No verifier infrastructure fault in any run |
| `ORC-011` | Every run emits the exact 45-check receipt |
| `ORC-012` | Every run scores exactly `1.000000` |
| `ORC-013` | All 45 individual outcomes are true |
| `ORC-014` | Sanitizer and applicable concurrency checks pass |
| `ORC-015` | Repeated outcomes are deterministic per standard |
| `ORC-016` | The full C++17/C++20 matrix passes |

Every rule result records its stable ID and version, severity, deterministic
confidence, observed value, expected value, evidence, and remediation.

## Receipt integrity and cache

Receipts bind the task descriptor, starter tree, private reference tree, hidden
grader, prompt hash, configuration, compiler/runtime fingerprint, six run
outcomes, exact check maps, and ORC results. `certification_sha256` excludes only
wall-clock duration, so timing noise does not change semantic certification.

The optional content-addressed cache accepts only certified, integrity-checked
receipts whose task, inputs, configuration, and environment reproduce the cache
key. A reference, starter, prompt, grader, compiler, sandbox, or configuration
change forces re-execution.

```bash
python3 -m glm47_posttraining.integrations.miles_aider_polyglot build-data \
  --tasks-dir /workspace/assets/aider-shadow/tasks/aider_polyglot_cpp_shadow \
  --out /workspace/assets/prepared-aider-253 \
  --oracle-workers 8 \
  --oracle-cache-dir /workspace/assets/aider-oracle-cache \
  --force
```

## Migration boundary

The previously published schema-v1 shadow archive contains no canonical
references and is intentionally rejected by this gate. A schema-v2 private
archive containing `.reference` packages must be generated, independently
reviewed, checksum-pinned, and published before Modal/Lium rebuilds can use the
new validator. Existing already-materialized answer-free datasets remain
readable, but they are not retroactively oracle-certified.

## Deferred milestones

The next dependency-ordered additions are:

1. grader determinism, portability, undefined-behavior, and assertion-quality
   validation;
2. adversarial anti-cheat and malicious-completion regression suites;
3. reward-density and hidden-partition independence analytics;
4. curriculum and dataset-level capability diversity validation.

LoRA projection scoring and token-entropy loss masking remain model-dependent
research/trainer concerns and are not oracle certification rules.
