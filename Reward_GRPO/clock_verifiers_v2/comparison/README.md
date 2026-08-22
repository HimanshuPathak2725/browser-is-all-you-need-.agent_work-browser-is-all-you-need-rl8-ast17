# Original versus v2 Clock verifier comparison

This experiment uses one strict-contract perfect baseline, fourteen deterministic faulty candidates, and one separately labeled dataset control. `generate_samples.py` recreates every candidate and `manifest.json` records the intended fault plus source hashes.

The canonical baseline is the pinned `.meta/example.h/.cpp` solution because both verifier packs accept it. The dataset control is the officially passing Luna `a01-clock-turn2` response; it is excluded from fault-detection denominators because its public signatures differ from the strict Clock contract used by both verifier packs.

## Generate

```bash
python3 generate_samples.py \
  --dataset-jsonl ../../../results/luna-fixed26-20260805/datasets/terminal_eval_only_samples.jsonl
```

The generator refuses unexpected baselines and replaces the complete `samples/`, `controls/`, and `manifest.json` outputs deterministically.

## Experimental units

- Positive control: `baseline/canonical/`
- Non-faulty dataset control: `controls/dataset_official_pass/`
- Faulty candidates: `samples/f01_*` through `samples/f14_*`
- Fixed task assets are not copied here; testing agents materialize each candidate over the same authenticated pinned exercise fixture.

Official behavior and strict-contract correctness are reported separately. In particular, `minus`, the default argument to `at`, and the required free form of `operator!=` are contract requirements not fully distinguished by the official test suite.
