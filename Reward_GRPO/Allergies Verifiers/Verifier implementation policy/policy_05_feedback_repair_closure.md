# Policy 5 — Feedback-Repair Closure

This policy authenticates a two-turn Allergies repair and decides whether the model removed one exact observed diagnostic, avoided leaving a compile or link failure, and reached a complete 50-test pass. It covers two evidence-backed repair classes: the older enum-versus-string API mismatch and the Midband-RL-v2 trial-1 missing-`<unordered_map>` include. It does not match arbitrary compiler output.

## Kernel table

| Kernel | Verifier function | What it asks | Exact implementation | `+1` condition | `-1` condition | Evidence |
|---|---|---|---|---|---|---|
| 5A | `verify_5a_bundle_integrity()` | Is the trajectory evidence complete and hash-bound? | Validate the manifest, safe relative paths, regular files, SHA-256 values, task identity, both turn receipts, and receipt-to-source/output hash bindings | Every required binding is valid | Not used; corrupt evaluator evidence is `INVALID` | Manifest, artifact hashes, task identities |
| 5B | `verify_5b_feedback_binding()` | Was the exact generated feedback delivered to turn 2? | Compare generated and delivered feedback byte-for-byte | Both are nonempty and identical | Not used; missing or changed feedback is `INVALID` | Both feedback files and hashes |
| 5C | `verify_5c_reported_diagnostic_removed()` | Did the repair remove the declared observed failure? | Classify turn-one output as exactly `api.is_allergic_to.parameter_type` or `build.missing_unordered_map_include`, bind it to `manifest.repair_class` when declared, and require that same class to be absent at turn two | One supported class is authenticated at turn 1 and absent at turn 2 | The declared diagnostic remains | Both score receipts, manifest, and normalized diagnostic ID |
| 5D | `verify_5d_official_consumer_compile()` | Did the repaired candidate pass the complete official consumer build? | Require authenticated turn-2 compile and link stages to succeed | Turn-2 return code is 0 and no compile/link diagnostic remains | Candidate still fails compilation or linkage, including list-return incompatibility | Turn-2 output, return code, diagnostic IDs |
| 5E | `verify_5e_complete_suite_closure()` | Did the repair reach the complete pinned suite? | Require a successful receipt whose output proves 50 assertions in 50 test cases | Status is `passed`, return code is 0, and the exact 50/50 summary is present | Completed candidate evaluation fails, times out, or lacks complete 50/50 success | Turn-2 score receipt and output hash |

## Trajectory bundle contract

```text
manifest.json
turn_1/
├── response.txt
├── source/allergies.h
├── source/allergies.cpp
├── score_receipt.json
└── generated_feedback.txt
turn_2/
├── delivered_feedback.txt
├── response.txt
├── source/allergies.h
├── source/allergies.cpp
├── score_receipt.json
└── source.diff
```

The manifest contains `schema_version`, `task_id`, `trajectory_kind`, and an `artifacts` object. It may declare `repair_class`; when present, that value must match the diagnostic authenticated from the turn-one receipt. Each required artifact entry contains a safe relative `path` and lowercase SHA-256 value. `trajectory_kind: single_turn` makes the policy explicitly excluded; omission of required evidence from a declared two-turn bundle is `INVALID`.

## 5A — Bundle integrity

All paths are resolved beneath the bundle without symlinks. JSON receipts must be objects and must identify task `allergies` or `local-aider-cpp/allergies`. Each receipt’s candidate-file hashes must match that turn’s source snapshot, and its output hash must match the recorded output. Hash or identity disagreement is evaluator failure, never candidate `-1`.

## 5B — Exact feedback delivery

Generated and delivered feedback must be byte-identical and nonempty. A candidate cannot be penalized for missing, truncated, or rewritten evaluator feedback.

## 5C — Reported diagnostic removal

The API class is recognized only from `is_allergic_to` plus the parameter-type diagnostic involving a string or character-array argument. The include class is recognized only when `allergies.h`, `unordered_map`, `does not name a template type`, and `<unordered_map>` all appear. One supported class must be present at turn one and the same class must be absent at turn two. Unknown diagnostics are evaluator `INVALID`, not candidate failure.

## 5D — Official consumer compilation

Turn 2 must complete compilation and linkage. Compiler markers such as `error:`, `undefined reference`, `linker command failed`, or a nonzero return code are candidate failure when the authenticated receipt reports a completed evaluation.

## 5E — Complete suite closure

The final receipt must record `status: passed`, return code 0, and the exact Catch summary `All tests passed (50 assertions in 50 test cases)`. Removing only the first diagnostic is insufficient.

## Aggregation

```text
applicable kernels = 5 for a two-turn trajectory
maximum kernel sum = +5
PASS           = all five kernels are +1
FAIL           = at least one candidate kernel is -1 and none is INVALID
INVALID        = at least one kernel is INVALID
NOT_APPLICABLE = trajectory_kind is single_turn; excluded from all denominators
```

## Execution

```bash
python3 "Reward_GRPO/Allergies Verifiers/verifiers/verifier_05_feedback_repair_closure.py" \
  --bundle-dir /path/to/allergies-trajectory \
  --output-dir /new/output/policy-05
```
