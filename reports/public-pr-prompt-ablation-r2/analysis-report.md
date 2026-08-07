# Public-PR prompt ablation v2 and v4 evaluation handoff

## Outcome

The compact v4 lane is ready for a fresh GCP image build and one evaluation run. A fresh model result is **not completed** and no model-success claim is made here.

This is a public-patch diagnostic, not clean generalization evidence and not training data. The historical v2 and v3 JSONL files and prompt artifacts remain unchanged.

## Evidence reviewed

| Artifact | Bytes | SHA-256 | Use |
| --- | ---: | --- | --- |
| Handoff proposed prompt | 7,063 | `b3997db3f5148890b879db2807c9a3c8de6f5be0552954cef529d8110c86ed25` | Capability-accurate compact prompt and primary-failure analysis |
| Baseline-preserving v3 prompt | 13,717 | `0069f527919eda1a6f8d5c2ed178858fcc2498b91c6efb4cea6aa44379c21d6c` | Exact helper bodies, insertion anchor, and concrete formatter call shapes |
| Final v4 prompt | 9,961 | `c2e80dccbd50d0c9e1e38ba06a4c021821ac82fb16ba500ac0358a4fe5e9ced5` | Final model-facing prompt |
| Immutable v4 JSONL | — | `03ed4454a8953b80b09325392c0045e9ea0ba64b6c483ea886c3850ffbd7c7a3` | Reproduction contract |

The external handoff source was read from `/opt/glm47-public-pr/fmtlib-prompt-tuning-handoff`. Its prompt digest is bound into the v4 JSONL prompt contract.

## Ablation conclusion

| Condition | Evidence-backed strength | Remaining problem | v4 decision |
| --- | --- | --- | --- |
| Earlier concrete baseline | Correct implementation direction and concrete code shapes | Namespace placement and qualification were not locked tightly enough | Preserve exact helper bodies and exact lexical insertion anchor |
| Handoff compact proposal | Removes unavailable tool claims and focuses on structural failures | Omits the concrete helper bodies that previously guided the right implementation | Use its concise boundary and migration ledger, then restore baseline shapes |
| v3 baseline-preserving prompt | Protects helper bodies, fallback overloads, preprocessor structure, and root call shapes | Longer than needed; the runner still permitted Aider's opaque auto-lint repair loop | Remove repeated workflow/audit blocks and disable auto-lint only for v4 |
| v4 compact merged prompt | Keeps task-specific shapes and locks while removing generic workflow load | Requires a fresh model run to determine outcome | Selected for the next controlled run |

The v4 prompt is smaller than v3 while retaining the exact implementation details that the raw compact proposal intentionally omitted. It contains no generic W01–W38 or F01–F12 block and does not instruct the model to claim unavailable compilation, search, terminal, or probe actions.

## Final model-facing controls

The final prompt:

- changes only `include/fmt/chrono.h`;
- anchors new helpers inside the first existing `detail` namespace, immediately before its pre-export close;
- supplies the exact arithmetic trait, checked/mixed cast overloads, and direct `to_time_t` body;
- freezes all four callable portability fallback overloads and `FMT_NOMACRO` behavior;
- names the complete fractional, millisecond, formatter-internal, system-clock, and local-time migration ledger;
- preserves C++11, preprocessor, namespace, overload, negative-remainder, and feature-gate invariants;
- states that validation is external and that one sanitized compiler diagnostic may arrive later;
- ends with ten task-specific structural checks rather than a generic repository workflow.

The model-facing source is `reports/public-pr-prompt-ablation-r2/final-prompt.md`. The builder embeds those exact bytes and the validator recomputes the embedded prompt digest.

## Harness changes

The suite name is `fmtlib-compact-repair-bestof4`. It remains exactly one task.

1. Candidate seeds are `1701`, `1702`, `1703`, and `1704`.
2. Every candidate starts from a fresh prepared repository copy.
3. The initial edit uses temperature `0.7`.
4. A failing candidate receives at most one repair turn at temperature `0.2`.
5. The repair turn exposes only the first sanitized compiler diagnostic rooted in the editable production header; private tests, probes, expected output, and evaluator-only paths are suppressed.
6. Aider auto-lint and auto-test are disabled for v4, preventing an opaque internal lint loop from rewriting a candidate. Historical lanes retain their previous defaults.
7. Evaluation stops at the first complete executable pass.
8. If every candidate fails, selection uses only the furthest executable stage. Reference-patch similarity and textual checklist coverage are diagnostic and cannot select a candidate.
9. Each attempt receipt records observed Aider token-usage markers as a model-call count when those markers are present.

This is candidate isolation, not a claim that every internal Aider diff block is transactionally atomic. Aider can still reflect on malformed diff edits; those calls are now observable, while each new candidate remains isolated from the others.

## Executable authority and privacy

Scope, warning-clean C++11 build, public chrono tests, and the independent probe are the authoritative gates. The reference patch and checklist are retained only for post-run diagnosis. The v4 prompt and repair messages do not expose reference code, private-probe source, hidden expected output, or evaluator internals.

The Docker image build binds the JSONL hash and replays base-fail, reference-pass, and plausible-wrong-fail controls before the runtime image is accepted.

## Validation evidence

| Gate | Result |
| --- | --- |
| Deterministic v4 regeneration and byte comparison | PASS |
| v4 SHA-256 sidecar | PASS |
| Static contract/prompt validation | PASS |
| Focused public-PR tests | PASS — 22 tests |
| Full repository test suite | PASS — 413 tests |
| Python compileall | PASS |
| Ruff on changed evaluator surfaces | PASS |
| Local executable oracle replay | NOT_COMPLETED — the host has no `cmake`; the pinned Docker build remains the required oracle gate |
| Fresh GCP model inference | NOT_COMPLETED |

## Next-run acceptance rule

Build a new image from the exact v4 bundle. Do not reuse the prior v3 image digest. Start one run with `SUITE=fmtlib-compact-repair-bestof4`. Accept the evaluator outcome only if the image build completes its bound static/oracle stages and the runtime receipt is present. Preserve all candidate and repair artifacts whether the task passes or fails.
