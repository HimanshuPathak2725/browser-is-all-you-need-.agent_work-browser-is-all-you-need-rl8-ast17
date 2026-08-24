# Clock verifier validation report

The final Clock package contains six independently executable policies. C01-C05 provide granular build, API, integration, formatting, and semantic signals; C06 authenticates the protected benchmark assets and runs the complete official suite. The aggregate runner records every policy while keeping task correctness separate from shaping diagnostics.

The verifiers were created from the pinned Clock contract, observed model failure families, and controlled fault injection. Overlapping checks were consolidated so each policy owns a clear boundary, evaluator failures remain `INVALID`, and only authenticated terminal success can establish official correctness.

## Final verifier set

| Policy | Boundary | Why it exists |
| --- | --- | --- |
| CLF-C01 | C++17 build and dependency integrity | Rejects invalid language mode, incomplete includes, warnings, and basic link failures |
| CLF-C02 | Exact public API | Checks required signatures, constructor visibility, default arguments, and free inequality |
| CLF-C03 | Integration and ODR | Exercises repeated includes, multiple translation units, linkage, and state isolation |
| CLF-C04 | Formatting and observation | Checks canonical rendering, signed boundaries, and stable const observation |
| CLF-C05 | Time properties | Checks construction, normalization, arithmetic, and equality relations |
| CLF-C06 | Official terminal suite | Authenticates protected assets and runs all official Clock tests |

## Creation method

1. Pin the benchmark contract, compiler mode, protected assets, and required public API.
2. Group observed failures by the boundary that can identify them without depending on another category.
3. Build independent compile, link, execution, and property probes for those boundaries.
4. Keep candidate failures distinct from missing tools, altered assets, malformed receipts, and other evaluator faults.
5. Preserve the complete official suite as the terminal oracle and expose stricter canonical conformance only as an explicit mode.

Each consolidated contract and its implementation rationale is in [`Verifier implementation policy/`](Verifier%20implementation%20policy/).

## Validation summary

| Control | Result |
| --- | --- |
| Canonical reference | Passed all 6 policies and 18 kernels |
| Expanded targeted fault set | 23/23 rejected in strict mode |
| Prior comparison fault set | 14/14 remained rejected in strict mode |
| Official-only fault | Passed shaping policies and failed C06, confirming the terminal gate is independently necessary |
| Altered protected assets | Reported `INVALID`, not candidate failure |
| Missing compiler | Reported `INVALID`, not candidate failure |

These aggregate results show that the final package preserves the tested coverage while using one consolidated verifier set. They do not claim complete coverage of every future implementation or adversarial candidate.

## Reward semantics

The runner defaults to `--acceptance-mode official`. In this mode, authenticated C06 success determines `reward_ready`; C01-C05 remain available as shaping and diagnostic signals.

Use `--acceptance-mode strict` only when the training objective requires the pinned canonical API and every shaping policy to pass. Both modes reject invalid evaluator state rather than assigning candidate reward.

## Run

```bash
python3 "Reward_GRPO/Clock Verifiers/verifiers/run_all.py" \
  --exercise-dir /path/to/pinned/clock \
  --output-dir /new/empty/output
```

Add `--acceptance-mode strict` for canonical conformance. The output directory must be new and empty so receipts from different candidates cannot be mixed.

## Conclusion

The final package has one terminal correctness gate, five focused shaping boundaries, deterministic receipts, and explicit invalid-state handling. The remaining boundary is production calibration: category rewards should be shadowed on unseen model outputs before they are assigned training weights.
