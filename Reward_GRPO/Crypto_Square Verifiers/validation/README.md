# Crypto Square verifier audit corpus

This directory is evaluator-only evidence. It is not imported by the dataset builder, added to prompts, or exposed to model responses.

`failure_gap_manifest.json` selects 49 preserved outputs from `crypto-square-kernel12-grpo20-rerun-20260821T173527Z`: all 20 outputs that fully passed the old 12-kernel verifier, one representative of every authenticated old-verifier bit vector, and representatives of both observed crash classes. `cases/` stores exactly the two editable candidate files for each selection. `failure_gap_replay_receipt.json` is the frozen replay result.

`control_validation_receipt.json` records the positive reference, an alternate-valid private-field rename, targeted semantic mutations, protected-test tampering, missing-compiler behavior, repeatability, and source immutability across all six standalone policies.

Run the failure-gap replay in the pinned GCC 13.3 verifier image:

```bash
OUT="$(mktemp -d /tmp/crypto-square-gap-replay.XXXXXX)"
chmod 0777 "$OUT"
docker run --rm --network none --read-only --cap-drop ALL \
  --tmpfs /tmp:rw,exec,nosuid,nodev,size=4g \
  -e STRANGE_ISOLATED_REPLAY=1 \
  -v "$PWD:/workspace:ro" \
  -v "$OUT:/evidence:rw" \
  glm47-reward-grpo-bank-account@sha256:e4d1090d07cab73e5c4137637beccebe1dac0f6aa440e7d4cbfc466c4f226932 \
  python3 '/workspace/Reward_GRPO/Crypto_Square Verifiers/validation/run_failure_gap_audit.py' \
    --output-dir /evidence --workers 8
```

Run the control validation under the same isolation and compiler identity:

```bash
OUT="$(mktemp -d /tmp/crypto-square-controls.XXXXXX)"
chmod 0777 "$OUT"
docker run --rm --network none --read-only --cap-drop ALL \
  --tmpfs /tmp:rw,exec,nosuid,nodev,size=4g \
  -e STRANGE_ISOLATED_REPLAY=1 \
  -v "$PWD:/workspace:ro" \
  -v "$OUT:/evidence:rw" \
  glm47-reward-grpo-bank-account@sha256:e4d1090d07cab73e5c4137637beccebe1dac0f6aa440e7d4cbfc466c4f226932 \
  python3 '/workspace/Reward_GRPO/Crypto_Square Verifiers/validation/run_control_validation.py' \
    --output-dir /evidence --workers 4
```

The runners refuse to start without `STRANGE_ISOLATED_REPLAY=1`, require an empty output directory, authenticate candidate and protected-test bytes, and keep all generated logs and receipts outside the candidate corpus.
