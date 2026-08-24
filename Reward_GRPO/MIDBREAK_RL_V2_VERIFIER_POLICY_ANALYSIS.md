# Midbreak-RL-v2 task-specific verifier analysis

This analysis uses the four `midbreak-RL-v2` Fixed26 evaluation histories and the pinned Polyglot task contracts. The task-generation pipeline is deliberately excluded because it is not part of verifier design. The already validated Policies 1–3 remain the compile/API foundation, broad semantic probe, and authenticated official-suite gate; the policies below add finer reward boundaries where the evaluation showed recurring or high-impact faults.

The eval histories also contain model context-exhaustion events. Those events explain why some second-turn repairs did not happen, but they are trajectory metadata rather than candidate C++ behavior. They belong in run analysis and are not converted into a source-code reward kernel.

| Task | Four-trial evidence | Fault pattern observed | Additional contract risks | Added policies |
|---|---|---|---|---|
| Circular Buffer | Final success 2/4 | Empty and full were confused; overwrite incorrectly changed fullness; initial clear broke later wraparound | FIFO lifecycle, generic value type, read/write capacity transitions | 4: empty/full lifecycle; 5: overwrite/clear wraparound |
| Clock | Final success 2/4 | `24:00` was not canonicalized; repairs introduced duplicate definitions, illegal writes in a `const` observer, and instance access in static `at()` | Large positive/negative minute arithmetic and normalized equality | 4: canonical arithmetic; 5: factory/observer/ODR discipline |
| Complex Numbers | Final success 1/4 | Free scalar/equality/stream operators repeatedly accessed private members or stale member names | Both scalar operand orders, complex division, magnitude, conjugate, exponential | 4: free-operator/public-observer contract; 5: scalar and numerical matrix |
| Crypto Square | Final success 1/4 | Missing `cipher` API, mismatched normalization declaration, missing `<cmath>`, and mutation from a `const` method | Exact empty and incomplete-row padding, normalization, square dimensions | 4: staged normalization and byte-exact layout |
| D&D Character | Final success 3/4 | Integer truncation produced wrong negative modifiers; repair moved `ability()` into a header without `inline`, causing multiple definitions | Roll range, best-three-of-four range, hit-point derivation | 4: signed floor and one-definition generation contract |
| Parallel Letter Frequency | Final success 2/4 | Missing `<execution>`/`<cctype>`; one attempt used `isalnum` and would count digits | Empty input, case folding, aggregation, large deterministic workload | 4: dependency and filtering contract; 5: aggregation/repeatability |
| Phone Number | Final success 3/4 | A data member collided with a member-function name and the repair never compiled | 10/11-digit rules, letters/punctuation, NANP area/exchange prefixes, formatting | 4: declaration separation and validation partitions |
| Robot Name | Final success 1/4 | Helper declaration did not match definition; other attempts exhausted too early or emitted an invalid name at a carry boundary | Stable names, reset, uniqueness beyond 1,000 names, complete prefix carry | 4: construction/reset lifecycle; 5: carry and namespace progression |
| Spiral Matrix | Final success 2/4 | Missing public function declaration, then repeatable SIGSEGV at size 2 | Exact small matrices, bounds safety, permutation/shape, extended oracle | 4: minimal-size bounds safety; 5: sanitized extended oracle |

## Scoring boundary

Every added kernel returns `+1` only when its exact compile/run evidence passes and `-1` for a candidate-caused failure. Missing tools, altered fixed tests, broken evaluator startup, or changed candidate source during verification remain `INVALID`; they never become a candidate reward. The official suite in Policy 3 remains the authoritative terminal correctness gate.
