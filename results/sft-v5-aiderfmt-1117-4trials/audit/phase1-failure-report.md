# Phase 1: SFT-v5 Aider Fixed-26 Failure Analysis

This audit follows the four SFT-v5 evaluation trials from archived model conversations through first-attempt outcomes, feedback retries, terminal compiler/test results, and finally an error taxonomy. The audited unit is one two-turn trajectory for each of 26 C++ tasks in each of four trials: 104 trajectories and 184 actual attempts.

The bundle is internally consistent and the SFT checkpoint is materially better than the PDF base evaluation, but 63/104 trajectories still fail after feedback. The dominant observable failure is compile-time interface/type breakage, while one persistent task (`all-your-base`) is invalid as a clean model-quality signal because its injected prompt contradicts its pinned tests and reference solution.

## Primary evidence table

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
| --- | --- | --- | --- | --- |
| Bundle integrity | Establishes the denominator and provenance | **Verified:** 4 trials, 104 paired task/chat records, identical 26-task sets, checksums valid | Run `python3 results/sft-v5-aiderfmt-1117-4trials/audit/verify.py` | `manifest.json`, `checksums.sha256`, `audit/verify.py` |
| Compile failures | Candidate reaches the compiler but violates C++ declarations, types, includes, access, or `-Werror` | **36/63 terminal failures (57.1%)**; examples include missing `abs`, invalid iterator declarations, Boost type misuse, redefinitions, and missing operators | Inspect the final CMake block in each archived `.aider.chat.history.md`; regenerate `failure-inventory.json` | Highest-priority SFT target: header/source-consistent compiler-repair rows |
| Link failures | Template declarations and definitions are split incorrectly or required instantiations are absent | **2/63 terminal failures (3.2%)**: `a2/circular-buffer` and `a8/linked-list` | Search terminal logs for `undefined reference` | Teach header-resident template implementations and explicit-instantiation trade-offs |
| Test/runtime failures | Code builds, but behavior, edge cases, state transitions, or exception policy are wrong | **25/63 terminal failures (39.7%)**; includes wrong values, unexpected exceptions, SIGSEGV, and SIGFPE | Inspect terminal Catch2 `FAILED` blocks and expansions | Add task-family semantic and failure-conditioned repair examples |
| Evaluator contract defect | The model is instructed to implement behavior that the hidden tests reject | **4/4 `all-your-base` trajectories affected**; prompt says invalid input returns `{}`, while tests/reference require `std::invalid_argument`; prompt also encourages `{0}` for zero while tests expect `{}` | Compare overlay lines 104-115 with pinned Polyglot `.meta/example.cpp` and terminal test output | Fix contract text, invalidate/re-run this task across all checkpoints, and exclude its current score from model-only conclusions |
| Feedback repair | Measures whether the second turn can use compiler/test feedback | **17/80 initial failures recovered (21.2%)**; 63 remained failed | Sum `FP` outcomes in `failure-inventory.json` | Train on minimal repair turns, especially compile diagnostics; preserve exact whole-file format |
| Operational output quality | Generation errors overlap with semantic/compile outcomes | Across 104 trajectories: **5 error outputs, 3 context exhaustions, 2 malformed responses, 0 test timeouts**; these occur in only five trajectories and overlap | Inspect result counters for `a2/a4 perfect-numbers`, `a4 clock`, `a4 diamond`, and passing `a5 space-age` | Do not add these counters as exclusive failures; reduce retry-context growth and validate format before evaluation |
| Persistent hard-task set | Tasks never solved in any of four trials, even with feedback | **7/26 tasks:** all-your-base, circular-buffer, clock, complex-numbers, kindergarten-garden, meetup, zebra-puzzle | Select tasks with `pass_at_2 == 0` in the inventory | Build the first targeted SFT slice around the six valid hard tasks; repair evaluator contract before using all-your-base |

## Run-level results

| Trial | Attempts | Pass@1 | Pass@2 with feedback | Turn-2 recoveries | Well formed | Error outputs | Context exhausted | Malformed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| a2 | 44 | 8/26 | 12/26 | 4 | 25/26 | 1 | 0 | 1 |
| a4 | 48 | 4/26 | 10/26 | 6 | 25/26 | 3 | 2 | 1 |
| a5 | 46 | 6/26 | 11/26 | 5 | 26/26 | 1 | 1 | 0 |
| a8 | 46 | 6/26 | 8/26 | 2 | 26/26 | 0 | 0 | 0 |
| **Aggregate / mean** | **184** | **24/104; 6/26 mean (23.1%)** | **41/104; 10.25/26 mean (39.4%)** | **17/80 initial failures** | **102/104 (98.1%)** | **5 total; 1.25/trial** | **3 total; 0.75/trial** | **2 total; 0.5/trial** |

Against the required PDF base row, the candidate improves mean Pass@1 from 0/26 to 6/26 (**+6 tasks, +23.1 percentage points**) and mean Pass@2 from 4/26 to 10.25/26 (**+6.25 tasks, about +24.0 points**). Well-formed output falls from 100% to 98.1%. The candidate is therefore improved on task success, with a small formatting regression. The comparison is indicative rather than seed-matched: the base row is one reported evaluation, while the candidate values average four stochastic trials.

## Exhaustive terminal symptom taxonomy

The following categories are mutually exclusive and cover all 63 terminally failed trajectories:

| Terminal symptom | Count | Share of 63 | What the check proves | What it does not prove |
| --- | ---: | ---: | --- | --- |
| Compile failure | 36 | 57.1% | Final candidate did not compile under C++17 plus `-Wall -Wextra -Wpedantic -Werror` | The first compiler line may be downstream of an earlier API/design error |
| Link failure | 2 | 3.2% | Compilation completed but required symbols were unavailable to the linker | It does not distinguish accidental omission from misunderstood template placement by itself |
| Test or runtime failure | 25 | 39.7% | Final candidate built and then failed an assertion or crashed | Hidden-test failure alone does not prove whether prompt, model, or test contract is wrong |
| **Total** | **63** | **100%** | Every terminal failure has one observed symptom | Root-cause families below overlap and must not be summed |

Five warning-as-error cases are directly visible within compile failures: `a2/clock`, `a4/diamond`, `a5/clock`, `a5/kindergarten-garden`, and `a5/zebra-puzzle`. This is useful because these are often repairable with compact compiler-feedback examples rather than new algorithm teaching.

## Root-cause families

These families explain the failures but intentionally overlap.

1. **Public API and header/source inconsistency — dominant model-side cause.** Missing methods, wrong member names, wrong Boost types, mismatched declarations/definitions, undeclared operators, and redefinitions account for much of the 36 compile failures. Representative evidence: `complex-numbers` lacks/loses `abs`; `zebra-puzzle` omits or breaks `solve`; `kindergarten-garden` loses `Plants`/`plants`; `binary-search-tree` emits invalid iterator types.

2. **Template placement and linkage.** `circular-buffer` and `linked-list` place template definitions where test translation units cannot instantiate them; `binary-search-tree` also repeatedly breaks nested iterator declarations. These require C++-specific SFT examples, not generic algorithm rows.

3. **Algorithm and edge-case semantics.** Built candidates still fail padding/transposition (`crypto-square`), negative division (`dnd-character`), divisor sums (`perfect-numbers`), country-code/NANP validation (`phone-number`), ring-buffer overwrite order, spiral coordinates, full-house scoring, and constraint-solving completeness.

4. **State, lifecycle, and ownership semantics.** `bank-account` mishandles close/balance rules; `robot-name` has generator/uniqueness issues; `sublist` reaches a segmentation fault on boundary handling. These benefit from state-transition and invariant-driven training rows.

5. **Evaluator contract contradiction.** The injected `all-your-base` notes are directly inconsistent with the pinned tests/reference. This is evaluator contamination of the error signal, not evidence that the model ignored the provided contract.

6. **Repair-loop thrashing and context growth.** Terminal compile failures average about **55.9k prompt tokens**, versus **24.8k** for terminal test/runtime failures. Together with only 17/80 feedback recoveries, this suggests repeated broad rewrites and lint reflections are compounding interface errors. This is an inference from token totals and conversations, not a controlled causal measurement.

## Task coverage and targeted diagnosis

| Task | Pass@1 / 4 | Pass@2 / 4 | Dominant observed gap | Training or evaluator action |
| --- | ---: | ---: | --- | --- |
| all-your-base | 0 | 0 | Prompt/test contradiction; empty/zero and exception policy | Fix overlay and re-run; do not train on the contradictory prompt |
| allergies | 1 | 3 | Class/member API shape | Header-sensitive repair rows |
| bank-account | 0 | 2 | Lifecycle, balance reset/close policy, concurrency | State-machine plus mutex/exception examples |
| binary-search-tree | 0 | 1 | Nested iterator/template API | Header-only template and iterator examples |
| circular-buffer | 0 | 0 | Template linkage plus overwrite/read state | Header-resident implementation and transition tests |
| clock | 0 | 0 | Normalization, formatting, operators, includes, `-Werror` | Minimal compile repairs plus negative-wrap cases |
| complex-numbers | 0 | 0 | Header/source member drift and missing `abs` | Paired `.h`/`.cpp` contract examples |
| crypto-square | 0 | 1 | Transposition, padding, empty-input divide-by-zero | Boundary-focused algorithm repairs |
| diamond | 0 | 1 | Row layout/width and warning cleanliness | Output-shape tests plus `-Werror` repair |
| dnd-character | 0 | 2 | Negative integer division rounds toward zero | Contrastive negative-score examples |
| gigasecond | 1 | 1 | Boost date/time construction | Library-API-specific examples |
| grade-school | 3 | 4 | Mostly stable; feedback fully recovers | Keep as positive/repair exemplar |
| kindergarten-garden | 0 | 0 | Public enum/function API and row/name indexing | Exact-contract plus indexing examples |
| knapsack | 3 | 3 | Mostly stable; one redefinition | Filter duplicate definition patterns |
| linked-list | 2 | 3 | Template definitions unavailable at link time | Header-only template repairs |
| meetup | 0 | 0 | Boost Gregorian weekday/date API | Library type/signature examples |
| parallel-letter-frequency | 2 | 2 | Missing include/redefinition | Small compiler-feedback repairs |
| perfect-numbers | 1 | 1 | Divisor sum includes the number; malformed outputs in two trials | Semantic contrast plus format validation |
| phone-number | 0 | 1 | NANP cleanup, leading country code, validation order | Decision-table examples |
| queen-attack | 3 | 4 | Stable; feedback fully recovers | Keep as positive/repair exemplar |
| robot-name | 2 | 2 | Generator definition and uniqueness invariant | Static storage plus collision examples |
| space-age | 4 | 4 | Stable across all trials | Preserve as positive control |
| spiral-matrix | 1 | 1 | Coordinate/index logic and integer type/include | Small-size boundary examples |
| sublist | 1 | 3 | Empty/range boundary; one SIGSEGV | Iterator-bound and sanitizer-style repairs |
| yacht | 0 | 2 | Category parsing/container mismatch/full-house scoring | Enum/category and scoring decision table |
| zebra-puzzle | 0 | 0 | Missing/broken solve API and incomplete constraints | Exact public API plus complete constraint solver examples |

## Directly verified facts

- Checkout: `tirtha-env-stable-midband-RL-v2` at commit `0a96357266da5a093b770ba963d1e7a4e6c07a1b`; the Himanshu and Teraformer branch refs resolved to the same commit during this audit.
- Checkpoint adapter SHA-256: `9608cfe476b3bd2573ffd02f334f55a18e80a9de00a0581d1d6aacc54ad8972e`.
- Training manifest SHA-256: `db1df88ed80bf3b8db8c857ec2cec61228323609547a95082d5d53e0ed60ec4b`; dataset contains 1,117 rows over 3 epochs.
- Evaluation pins match the fixed-26 contract: Aider `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`, Polyglot `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`, two tries, temperature 0.7.
- The bundled verifier passed, and the deterministic inventory accounts for all 104 trajectories, 184 attempts, and 63 terminal failures.
- The exclusive 36 compile / 2 link / 25 test-runtime split is derived from the final CMake/Catch2 block of every terminally failed archived chat.
- The `all-your-base` contradiction is directly visible between `reproduction/aider_fixed26_contract_overlay.py` and the pinned tests/reference used by the run.

## Inferences from code, logs, and receipts

- Public API/header-source drift is the dominant underlying model problem because most terminal failures stop at compiler diagnostics about declarations, members, types, operators, or definitions.
- High prompt-token use on compile failures indicates repair-loop thrashing, but token volume alone does not prove that context length caused the final error.
- Targeting the six valid persistent hard tasks should yield more benchmark transfer than adding broad generic C++ rows; `all-your-base` must be repaired at the evaluator layer first.

## Unverified boundaries

- The archive deliberately excludes benchmark test files. The test behavior was verified against terminal logs and a fresh checkout of the pinned Polyglot commit, but the exact ephemeral shard filesystem was not preserved.
- No GPU/model rerun was performed, so reproducibility of stochastic scores and the effect of a corrected contract remain unverified.
- The report does not claim mutually exclusive root causes. A compile failure can simultaneously involve an API misunderstanding, a missing include, and a bad repair turn.
- The PDF base comparison is not a four-seed paired experiment. Treat small one-task differences as decoding variance unless repeated.
- The generic run-audit helper does not understand this receipt's `multi_turn_with_error_feedback_at_2` field, and the generic output diagnoser currently parses `.cpp` as `.c`; neither helper's raw generated draft was retained as evidence.

## Recommended Phase 2 queue

1. Correct the `all-your-base` contract, add a prompt-vs-test contract check, and re-run that task across base and SFT checkpoints.
2. Build a compiler-repair SFT slice from the 36 compile failures, led by the six valid persistent tasks and exact `.h`/`.cpp` pairs.
3. Add C++ template/linkage rows for circular-buffer, linked-list, and binary-search-tree.
4. Add failure-conditioned semantic repairs for crypto-square, D&D negative division, phone-number validation, perfect-numbers divisor boundaries, and stateful tasks.
5. Gate exported rows on parseable Aider whole-file format, compile success, and prompt/test contract consistency before training.
6. Re-run four matched trials and report both task-clustered confidence intervals and per-task transition counts.

## Conclusion

SFT-v5 clearly improves fixed-26 success over the PDF base, but its remaining failures are primarily interface-correctness failures rather than timeouts or infrastructure failures. The immediate risk is training on contaminated or weakly diagnosed feedback—especially the contradictory `all-your-base` contract—so the next concrete check is a corrected-contract rerun followed by a compiler-repair dataset built from the verified 36 compile and 2 link failures.
