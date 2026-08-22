# C09 instruction: repair-transition quality

## Observed failure

Clock recovered in 0/4 feedback trajectories. a4 and a8 replaced one failure with a different compile/API failure; a2 and a5 converged on the same warning category.

## Contract

Repair quality is evaluated from two immutable aggregate receipts, one before feedback and one after. The tool reports resolved, persistent, and regressed categories plus terminal transition (`FF`, `FP`, `PF`, or `PP`).

## Reward boundary

C09 is **diagnostic-only** in v2. It emits no `+1/-1` candidate reward because a source-only verifier cannot establish causal use of feedback, and stage-based partial rewards can be gamed. Reward enablement requires frozen trajectory snapshot provenance and an offline calibration study.

## Pass-like quality condition

The strongest transition is `FP`: terminal failure before feedback and authenticated terminal success afterward, with no invalid category receipts. Other transitions remain observations, not reward decisions.
