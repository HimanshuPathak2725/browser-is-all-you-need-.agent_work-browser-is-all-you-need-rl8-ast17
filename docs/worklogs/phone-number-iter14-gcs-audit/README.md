# Phone Number GRPO20 GCS audit

This worklog audits the training run
`phone-number-kernel12-grpo20-spot-20260822-102653` directly from its GCS
artifacts. It focuses on the exact failure mechanisms across the 20 recorded
rollout updates and keeps the eight-task training monitor separate from the
external Fixed26 evaluation.

## Source and identity

- GCS prefix:
  `gs://skypilot-filemounts-ubuntu-f0048940-88p8zkcq/phone-number-kernel12-grpo20-spot-20260822-102653`
- Remote inventory: 162 objects, 3,383,144,853 bytes.
- Run status: successful; 20 rollouts; training gate passed.
- Saved checkpoints: iterations 4, 9, 14, and 19.
- Iter14 adapter SHA-256 recorded by the training gate:
  `62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a`.
- The adapter hash is manifest-verified. Its 485,940,769-byte model file was
  intentionally not downloaded and therefore was not byte-rehashed locally.

The raw rollout set is 40 PT files (20 train and 20 monitor-eval dumps),
232,525,224 bytes total. Files were loaded only with
`torch.load(..., weights_only=True)`; unrestricted pickle loading was not used.

## Important naming caveat

The native PT payload has no `epoch` or `iteration` field. Both the filename and
payload provide the same zero-based `rollout_id` from 0 through 19. Therefore
the report uses **update**, not epoch. Checkpoint directories are separate and
must not be interpreted as proof that an internal monitor dump is a post-update
checkpoint evaluation; the run receipt says `post_update_eval=absent`.

## Headline findings

- Training: 2,885/5,120 strict all-kernel passes (56.35%). Update 9 was best
  at 157/256 (61.33%); update 0 was worst at 126/256 (49.22%). The first-five
  to last-five pass-rate change was +5.312 percentage points, but performance
  peaked at update 9 and did not improve monotonically.
- Failed training rows: 2,235 total, including 130 compile errors, 140
  format-invalid rows, 62 truncated generations, zero timeouts, and zero
  infrastructure errors. Compile/format/truncation flags can overlap.
- The three largest task-level failure mechanisms were
  `observed-member-function-name-collision` (594),
  `declared-members-not-defined` (558), and `missing-public-api` (498).
- Kernel `PH-E03-C` was the dominant failed kernel with 2,067 hits.
- Monitor eval: 92/160 passed (57.5%), but it contains only eight Phone Number
  training-monitor tasks per update and is **not Fixed26**.
- Integrity nuance: 33 training rows have `format_valid=false` while also
  recording `all_tests_pass=true`; one passed row is marked truncated. These
  are reported separately and are not counted as failed outputs.

See [per_update_failure_report.md](per_update_failure_report.md) for the complete
update table and [per_update_failure_report.json](per_update_failure_report.json)
for machine-readable counts.

## Fixed26 limitation

The four provided Fixed26 eval IDs were not found as exact top-level prefixes.
Recursive object-name searches across the configured runs bucket and every
project `skypilot-filemounts-*` bucket also returned no matches. Consequently,
the reported 11/15, 12/15, 11/15, and 11/16 trials remain summary-only evidence;
their task counts, tries, commits, adapter binding, and row-level failures have
not yet been independently verified.

## Included and excluded artifacts

This directory retains the compact report, its generator, source inventory,
schema summary, and small run/checkpoint receipts. It deliberately excludes:

- the 68 MB extracted row data;
- 222 MB of downloaded rollout dumps;
- checkpoint weights;
- `run.log`, which the source artifact manifest marks as `sensitive_content`.

The complete fetched copy remains under `/tmp/phone_iter14_gcs_audit` for the
current workspace session.
