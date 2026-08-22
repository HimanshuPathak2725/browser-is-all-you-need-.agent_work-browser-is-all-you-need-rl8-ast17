# Validation harness

`validate.py` reconstructs the pinned reference candidate in an external output directory, applies one controlled mutation per reward category, runs the complete C01-C08 pack, and verifies C09 on both recovery and regression transitions.

```bash
python3 validation/validate.py \
  --template-exercise-dir /path/to/pinned/clock \
  --output-dir /new/empty/validation-output
```

The template must contain authenticated non-candidate assets and `.meta/example.h/.cpp`. Fixtures, compiler logs, category receipts, aggregate receipts, and `validation_summary.json` are written below the requested output directory. Nothing is written into candidate source or this package.

The controlled mutations are diagnostic controls, not estimates of real-model error frequency. Passing them establishes known-fault sensitivity only; it does not prove absence of unknown false positives or false negatives.
