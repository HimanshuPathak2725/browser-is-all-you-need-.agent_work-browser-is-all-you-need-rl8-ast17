# Common characteristics across task-specific C++ verifiers

This report compares the 16 task-specific verifier packages under `Reward_GRPO` with the original seven-policy `Global Cpp Verifiers` package and the new G08-G10 framework additions. The evidence base is 99 task-specific policy documents, their validation reports, the four active global manifests, the multi-environment runner, and the pinned Aider Polyglot C++ task source at commit `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`. The goal is to identify and implement reusable verifier characteristics, not to launch or change GRPO.

The original global pack had a sound infrastructure boundary but an incomplete semantic boundary. G01-G07 covered candidate integrity, strict build, API/link, official behavior, sanitizer execution, trajectory evidence, and portability, but not the recurring header/ODR, task-owned edge/property, or lifecycle/repeatability families. G08-G10 now provide manifest-driven executors for those three families and reject mislabeled characteristic metadata. G08 has passed a two-topic validation campaign, while G09/G10 task probes and all active-manifest or training configuration changes remain pending. `C1`-`C10` below are stable cross-topic characteristic IDs, while `G01`-`G10` are global verifier policy IDs.

## Stable characteristic IDs

- **C1 — Candidate Evidence Integrity** -> existing **G01**
- **C2 — Strict Build Quality** -> existing **G02**
- **C3 — Public API and Link Contract** -> existing **G03**
- **C4 — Header, Dependency, and ODR Integrity** -> **G08 validated on Circular Buffer and Phone Number**, inactive pending manifest review
- **C5 — Official Functional Correctness** -> existing **G04**
- **C6 — Semantic Partitions and Metamorphic Properties** -> implemented framework **G09**, task probes pending
- **C7 — Lifecycle, State Isolation, and Repeatability** -> implemented framework **G10**, task probes pending
- **C8 — Safety, Bounds, Undefined Behavior, and Concurrency** -> existing **G05**
- **C9 — Toolchain Portability** -> existing **G07**
- **C10 — Trajectory, Feedback, and Harness Integrity** -> existing audit-only **G06**

| Common characteristic | Cross-topic evidence | Current global coverage | Gap or failure risk | Recommended control |
|---|---|---|---|---|
| Candidate and protected-asset integrity | Final Clock, Crypto Square, Diamond, Kindergarten Garden, and D&D packages authenticate fixed assets and distinguish evaluator faults from candidate faults. The same boundary appears throughout the older packages. | **Covered by G01.** Every global policy also calls the common manifest/hash preparation path. | G01 proves evidence integrity, not candidate correctness. A candidate can pass G01 while being uncompilable or semantically wrong. | Keep G01 as a prerequisite/diagnostic control, never as a stand-alone semantic success signal. |
| Warning-clean build and compilation | All 16 task-specific packages contain a compile, public-surface, or warning-clean boundary. Circular Buffer and Phone Number both begin with exact API/compile/link policies. | **Partly covered by G02.** The current `strict-build` mode compiles candidate `.cpp` files with C++17 warnings as errors. | Header-only implementations and defects exposed only when a public header is consumed can escape the G02 command. | Retain G02, but make applicability explicit and pair it with the proposed G08 header/integration policy. |
| Exact public API and external linking | API shape is a repeated boundary in all 16 packages. Observed examples include Phone Number declaration collisions, D&D non-inline definitions, missing Crypto Square methods, stale Complex Numbers free operators, and Spiral Matrix missing declarations. | **Partly covered by G03.** The current `api-link` mode compiles the official sources and tests, then stops before execution. | It is not an independent exact-signature probe and can miss contract details that the official caller does not instantiate. | Keep G03 for task-owned caller/link evidence; require manifests to supply an independent signature/caller command where the public contract has uncovered types, overloads, constness, or references. |
| Header self-containment, include hygiene, dependency isolation, and ODR | Direct policy or verifier evidence appears in at least 9/16 packages. A new two-topic campaign covered 5 valid, 8 targeted structural, 2 supplemental structural, and 8 semantic-only candidates. | **G08 validated but inactive.** All targeted faults reached their intended kernel; repeated-include and protected-dependency produced four incremental signals with zero valid false rejection. | A candidate may compile in the official translation-unit order while relying on transitive includes, defining non-inline header symbols, or including protected implementation/test assets. | Review Circular Buffer and Phone Number task manifests separately; do not change training routing as part of validation. |
| Authenticated official functional behavior | Official behavior is the terminal oracle in the mature packages and is deliberately kept separate from shaping diagnostics. | **Covered by G04.** It authenticates protected assets and runs the complete official command. | The official suite is necessary but not sufficient: measured campaigns found faulty candidates that passed official-only boundaries. | Keep G04 as the authoritative terminal gate. Do not merge its result with G01 or treat infrastructure validity as semantics. |
| Semantic boundary partitions, relations, and independent oracles | All 16/16 task-specific packages contain semantic behavior beyond compile/API structure. Circular Buffer separates empty/full and wraparound; Phone Number separates NANP partitions; Clock, Crypto Square, Diamond, Kindergarten Garden, and D&D use properties, broader domains, or independent oracles. | **G09 framework implemented but inactive.** It requires `C6` plus an edge-partition, relational-property, independent-oracle, or metamorphic-property label. | Errors outside official examples receive no specific signal, and very different fault families collapse into one terminal failure. This is the largest common coverage gap. | Populate G09 only with authenticated task-owned probes and independent expected values; the global framework must not invent semantics. |
| State transitions, lifecycle, isolation, and repeatability | Explicit primary controls appear in at least 8/16 packages: Circular Buffer, Robot Name, Grade School, Bank Account, Clock, Parallel Letter Frequency, Kindergarten Garden, and D&D Character. | **G10 framework implemented but inactive.** It requires `C7` plus a lifecycle, isolation, reset, or repeatability evidence kind. | Stateful candidates can pass isolated examples but fail after a transition sequence, leak state between objects/calls, or behave nondeterministically. | Populate G10 with contract-supported transition sequences, fresh-instance comparisons, resets, and repeated inputs without requiring a private representation or forbidden determinism. |
| Memory, bounds, undefined behavior, and concurrency safety | Explicit sanitizer or checked-domain controls appear in Bank Account, Grade School, Sublist, Spiral Matrix, Clock, Crypto Square, Diamond, and Kindergarten Garden; Circular Buffer and Parallel Letter Frequency add ownership/concurrency-relevant behavior. | **Covered structurally by G05**, which runs a manifest command under ASan/UBSan. | The four current manifests sanitize only the official suite. Safety defects outside its inputs remain invisible. | Keep G05, but let manifests add task-relevant stress commands from G09/G10 instead of merely rebuilding the same official cases under sanitizers. |
| Cross-compiler/toolchain portability | Bank Account, Grade School, and Sublist make portability explicit; build/API failures in other topics can also be compiler-sensitive. | **Covered by G07** through the manifest-selected alternate compiler. | Portability can become a false negative if a toolchain is missing or the task does not claim support. | Keep G07 optional. Missing tooling is `INVALID`; unsupported tasks should exclude the policy rather than fail the candidate. |
| Trajectory, feedback, and harness integrity | Allergies, Bank Account, Grade School, Perfect Numbers, and Sublist separate feedback/harness evidence from source correctness. | **Covered as audit-only G06.** It is excluded for the current single-turn dataset. | Context exhaustion or delivery failures are run telemetry, not properties of the final C++ files. Turning them into source reward would misattribute failure. | Keep G06 outside semantic acceptance and outside the proposed G08-G10 source-policy set. |

## Implemented framework ownership

- **G08 owns structural integration**, not task behavior. Each command must identify `C4`, a unique probe ID, and one of four structural evidence kinds.
- **G09 owns task semantics beyond the official examples**. Each command must identify `C6`, a unique probe ID, and an edge, relational, oracle, or metamorphic evidence kind; the framework does not invent semantics.
- **G10 owns stateful execution behavior**. Each command must identify `C7`, a unique probe ID, and a lifecycle, isolation, reset, or repeatability evidence kind.
- **G04 remains the terminal correctness gate**. G08-G10 are shaping and diagnostic signals until their false-positive rate and faulty-sample coverage are validated.
- **G01 remains evidence integrity**, not a semantic training policy. In the current config, each of the four global topics has only `G01` in `dataset_policies`; this is directly verified configuration state and should be reviewed only after G08-G10 validation, not changed as part of this report.

## Validation baseline and boundaries

Directly verified:

- The repository contains 16 task-specific packages with 99 policy documents, plus ten global policy/verifier pairs: seven original and three new inactive framework policies.
- Four topics currently use global manifests: Binary Search Tree, Linked List, Meetup, and Zebra Puzzle. Each manifest supplies one command for G02, G03, G04, G05, and G07.
- The existing unit contract passes `5/5`; static preflight passes for 17 topics and 73 policy environments with model-prompt/policy isolation.
- The G08-G10 executor tests pass `13/13`, including the authenticated infrastructure-invalid exit contract and malformed exit-schema controls.
- The combined global and multi-environment regression set passes `18/18`; G08 validation passes 23/23 candidate classifications, 4/4 invalid controls, 23/23 decision repeats, and the activation-readiness gate for manifest review.
- The checked-in `multi_env_global_canary_receipt.json` has status `failed` and includes an older five-topic routing that still contains Kindergarten Garden. It is historical evidence, not a current positive-control readiness receipt.

Inferred from code and validation evidence:

- G08-G10 capture the smallest reusable partition of the repeated topic-specific checks without forcing one implementation shape across unrelated tasks.
- Selecting integrity-only G01 as the sole dataset policy for global topics is weak semantic alignment, even though the runner also executes configured terminal policies. This is a design risk, not a locally proven cause of checkpoint regression.

Unverified:

- The reported best-checkpoint pass@1 regression from `11.25` to `9.5` is user-provided context; no matching run receipt was found or evaluated in this report.
- No claim is made about G09/G10 task coverage, G08 production routing, reward calibration, live worker behavior, or training improvement. G08 evidence currently applies only to Circular Buffer and Phone Number.

The 99 task-specific policies overlap heavily, so they are not 99 independent error families and their kernel counts must not be added as unique coverage. The dominant pattern is that the reusable executor/schema layer is generalized and C4 now has two-topic evidence, while C6/C7 probes remain task-owned and unvalidated. The next concrete step is review of validation-only G08 commands and evidence before any separate manifest activation proposal.
