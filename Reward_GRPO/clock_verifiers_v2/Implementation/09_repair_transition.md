# C09 implementation report: repair transition

`verifier_09_repair_transition.py` consumes two immutable `aggregate_receipt.json` files, verifies compatible schemas/category sets, and reports resolved, persistent, regressed, and invalid categories. It derives terminal transitions from authenticated C08 outcomes.

The recovery control produced `FP/recovered`; the reverse produced `PF/regressed`. Both receipts explicitly set `reward_eligible: false` and `kernel: null`, so trajectory heuristics cannot accidentally enter GRPO reward.

| Field | Meaning |
| --- | --- |
| `transition` | Before/after terminal state: FF, FP, PF, or PP |
| `resolved_categories` | Non-pass before, pass after |
| `regressed_categories` | Pass before, non-pass after |
| `persistent_failure_categories` | Non-pass in both receipts |
| `invalid_categories` | Evaluator-invalid before or after |

Production reward enablement is intentionally blocked until before/after snapshot provenance and offline correlation with human repair quality are validated.
