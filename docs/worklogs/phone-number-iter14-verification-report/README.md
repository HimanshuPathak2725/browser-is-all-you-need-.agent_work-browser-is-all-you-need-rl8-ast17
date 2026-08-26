# Phone Number kernel12 GRPO20 — complete verification report

Consolidated report for the public release `phone-number-kernel12-GRPO20`
(training run `phone-number-kernel12-grpo20-spot-20260822-102653`, scored
checkpoint `iter_0000014`). It merges the GCS training audit, the deep
row-level rollout-dump extraction, and the newly recovered Fixed26 evaluation
archives into one document.

Report generated 2026-08-26 from primary artifacts (GCS objects, PT rollout
dumps, W&B API, Hugging Face repo contents, PR #3 file contents).

## 1. Release identity

| Field | Value |
| --- | --- |
| Public release name | `phone-number-kernel12-GRPO20` |
| Training run ID | `phone-number-kernel12-grpo20-spot-20260822-102653` |
| Scored checkpoint | `iter_0000014` |
| Scored adapter SHA-256 | `62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a` |
| Training status | success; 20 rollouts; training gate `passed` |
| Fixed26 result | pass@1 `11.25/26 (43.27%)`; pass@2 `15.25/26 (58.65%)`; 4 trials / 104 samples |
| Hugging Face archive | `Terrano09/phone-number-kernel12-GRPO20` (adapters at iters 4/9/14/19 + `Phone_Number_train.jsonl`) |
| W&B run | `models-iit-bhu-news/glm47-phone-number-dnd-grpo/runs/phone-number-kernel12-grpo20-spot-20260822-102653` |
| Training config | `Reward_GRPO/phone_number_grpo_skypilot.yaml`, `Reward_GRPO/phone_number_grpo.py` |
| Eval config | `eval-job22-contractv2/phone-number-iter14-skypilot.yaml` (exists only in PR #3) |

## 2. Training configuration

- Base model `GLM-4.7-Flash` (revision `7dd20894…b67`), reference checkpoint
  `GLM-4.7-Flash_torch_dist_tp4_pp1_ep8`; Megatron TP4/PP1/EP8 on 8×H100
  (GCP `us-central1`, `a3-highgpu-8g`; `use_spot: false` despite the run name).
- Warm start: D&D Character GRPO20 iter-19 LoRA adapter, SHA-256
  `c9afe1ed…d766`, MTP-stripped to a hybrid adapter at launch.
- GRPO: 20 updates, rollout batch 8, 32 samples/prompt, global batch 256,
  seq len 12288, response len 8192, temperature 0.7, thinking on, LR 3e-5
  constant (0.1 warmup), KL coef 0.1, LoRA r16/α32/dropout 0 on
  `q_a_proj, kv_a_proj_with_mqa, o_proj, gate_proj, up_proj, down_proj`.
- Wall time 8,057 s (~2h14m); peak VRAM 70,342 MiB; checkpoints saved at
  iterations 4, 9, 14, 19.
- Curriculum: 8 answer-free Phone Number episodes (1 full-solve,
  5 bug-injection repairs, 1 missing-definitions repair, 1 eval-feedback
  repair); dataset kind `aider-polyglot-cpp-shadow-grpo`; data manifest
  SHA-256 `2c0e004d…d50c`.

## 3. Reward design and its measured defects

The hidden test prints an authenticated receipt
`GLM47_PHONE_KERNELS_V1:<12 bits>`; each kernel scores +1/−1 and
`reward = score = kernel_sum/12` where `kernel_sum = passed − failed`
(even values −12…+12). Infrastructure faults (infra error, or all-pass with
no authenticated receipt) map to reward 0.0 flagged `infrastructure_error`,
never to negative reward. Verified on all 5,280 rollout rows: the identity
`reward == score == kernel_sum/12` holds with zero exceptions.

Row-level extraction from the 40 PT dumps proves two design defects that the
earlier audit could only infer from aggregate counts:

- `{PH-E02-A, PH-E03-A, PH-E04-B}` agree on **5,120/5,120** train rows —
  provably the same test. `{PH-E01-A, PH-E04-A}` likewise agree on all rows.
  The gate string's "12 **independent** kernels" therefore reduces to at most
  9 effective signals (near-duplicates PH-E01-C and PH-E03-B disagree on 1
  and 5 rows respectively).
- The training-time `PH-E03` kernels (selected valid inputs / formatting /
  invalid inputs) do not match the standalone verifier's PH-E03 meaning
  (authenticated official assets/build/tests) — characteristic IDs are
  mislabeled relative to the verifier pack's policy documentation.

`PH-E03-C` is the dominant failed kernel (2,067 train failures, 85–119 in
every update). `failure_signature` is a per-task constant (design metadata),
not a per-row diagnostic.

## 4. Per-update × per-task training extraction

Source: 20 train dumps (`grpo_0.pt`…`grpo_19.pt`, 256 rows each) and 20
monitor dumps (`grpo_eval_0.pt`…`grpo_eval_19.pt`, 8 rows each), loaded with
`torch.load(weights_only=True)` only; extracted rows field-compared against
the raw PTs with 0 mismatches. Full CSVs:
`/tmp/phone_iter14_gcs_audit/deep_dive/` (session-local).

Train passes per update per task (32 samples per cell):

| Update | char-valid | country-code | eval-feedback | formatting | full-solve | length-part | missing-defs | nanp-prefix | Total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 15 | 25 | 1 | 25 | 4 | 26 | 4 | 26 | 126 |
| 1 | 18 | 17 | 2 | 23 | 4 | 31 | 3 | 30 | 128 |
| 2 | 21 | 24 | 0 | 29 | 4 | 27 | 3 | 26 | 134 |
| 3 | 23 | 16 | 1 | 32 | 5 | 27 | 5 | 32 | 141 |
| 4 | 22 | 23 | 2 | 30 | 6 | 24 | 2 | 31 | 140 |
| 5 | 27 | 23 | 2 | 29 | 8 | 29 | 4 | 30 | 152 |
| 6 | 21 | 19 | 1 | 30 | 7 | 23 | 3 | 30 | 134 |
| 7 | 22 | 25 | 2 | 28 | 4 | 27 | 3 | 30 | 141 |
| 8 | 22 | 20 | 1 | 32 | 8 | 28 | 7 | 31 | 149 |
| 9 | 24 | 22 | 5 | 30 | 9 | 30 | 7 | 30 | **157** |
| 10 | 25 | 24 | 2 | 28 | 6 | 27 | 2 | 30 | 144 |
| 11 | 16 | 25 | 1 | 32 | 8 | 26 | 3 | 31 | 142 |
| 12 | 24 | 22 | 3 | 31 | 12 | 29 | 2 | 30 | 153 |
| 13 | 25 | 28 | 3 | 31 | 9 | 27 | 3 | 30 | 156 |
| 14 | 21 | 26 | 1 | 30 | 8 | 27 | 7 | 31 | **151** |
| 15 | 22 | 25 | 3 | 30 | 4 | 29 | 3 | 32 | 148 |
| 16 | 19 | 18 | 3 | 31 | 11 | 28 | 6 | 31 | 147 |
| 17 | 19 | 22 | 4 | 31 | 10 | 28 | 3 | 30 | 147 |
| 18 | 22 | 24 | 6 | 30 | 5 | 27 | 7 | 30 | 151 |
| 19 | 20 | 21 | 3 | 29 | 10 | 24 | 5 | 32 | 144 |

- Overall 2,885/5,120 (56.35%). Best update 9 (157/256, 61.33%); update 14
  (the scored checkpoint) is 151/256 (58.98%); final update 19 declines to
  144/256 (56.25%). Mean reward peaks at update 9 (0.842).
- First-5 → last-5: every task improved, none degraded; but the three
  structural tasks stay near floor overall — eval-feedback-repair 7.2%,
  missing-definitions 12.8%, full-solve 22.2%. These three produced
  1,650/2,235 failures (73.8%) despite perfectly balanced sampling
  (640 rows per task).
- Failure anatomy of the 2,235 failed rows: 100% `kernel_tests_failed`;
  129 compile errors (returncode 1), 126 rows with no parseable candidate
  (returncode None), 1,966 ordinary semantic failures. **Zero timeouts, zero
  infrastructure errors.** 62 failed rows truncated (+1 passed row = 63 raw;
  one passed row sat exactly at the 8,192-token cap).
- 401 negative-reward rows. 12 distinct reward values observed.

Monitor eval (8 tasks × 20 updates, 92/160 = 57.5%): per-task totals —
length-partition 19/20, nanp-prefix 19/20, country-code 16/20,
formatting 16/20, char-validation 15/20, full-solve 5/20,
eval-feedback 2/20, **missing-definitions 0/20**. Critically,
`data/grpo/train.jsonl`, `data/eval/train_monitor.jsonl`, and
`data/eval/validation.jsonl` are **byte-identical** and every monitor row is
labeled `split: train` — the monitor is the training set, so it is
train-fit, not a held-out selection signal (the manifest itself declares it
"not checkpoint-selection evidence"). No data justified choosing iter 14
over iter 9.

Integrity anomalies (enumerated in `deep_dive/anomalies.json`): 33 train
rows with `format_valid=false` but `all_tests_pass=true` (all reward 1.0,
returncode 0 — a verifier-field inconsistency, not failed outputs); 1
passed-but-truncated row; 120 rollout rows never logged to W&B
(5,000 of 5,120; eval 160/160 logged); `timing_status: unverified` in both
receipt and evidence summary.

## 5. Fixed26 evaluation archives — recovered and row-verified

The earlier GCS audit searched only the `skypilot-filemounts-*` buckets and
reported the four trials as summary-only evidence. The eval config's durable
root is a different bucket, and all four archives are present there:

`gs://lifeandhalf-24122025-w8-biayn/runs/glm47/evaluations/aider-fixed26/phone-number-iter14-fixed26-thinking-spot-20260822-{142309,152052,172835,190309}/`

Each archive contains a run-level `run_receipt.json` with full per-task
`validation.outcomes`, model settings (thinking on, temp 0.7, max_tokens
32768, whole edit format), shard logs, 13 per-exercise result files per
shard (104 `.aider.results.json` total), shard receipts with overlay SHA-256
records, and adapter conversion receipts. All four trials `status:
complete`, completed 2026-08-22 at 15:12 / 16:40 / 18:54 / 19:44 UTC.

Verification verdict — **every claimed number confirmed exactly**, with
run-receipt outcomes matching all 104 per-exercise result files
(0 mismatches; no malformed responses; no test timeouts):

- pass@1: 11, 12, 11, 11 of 26 (mean 11.25/26, 43.27%)
- pass@2 (`pass_at_k`, tries=2): 15, 15, 15, 16 (mean 15.25/26, 58.65%)
- phone-number: turn-0 pass in all four trials
- Adapter binding: scored-adapter SHA-256 `62fa190a…575a` present in every
  run receipt, all 8 shard receipts, and all 4 conversion receipts; serving
  adapter `6d0cb2ef…ff67` (9,741→9,534 tensors); `lora_activation_verified:
  true`. Driver: aider `5dc9490…` (0.86.3.dev53), polyglot `7e0611e…`, eval
  set `fixed26-contract-v2`, training data manifest `2c0e004d…d50c`.

Per-task matrix (`1-` = passed turn 1; `01` = failed turn 1, recovered turn
2; `00` = never passed):

| Task | T1 | T2 | T3 | T4 | | Task | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all-your-base | 1- | 1- | 1- | 1- | | meetup | 00 | 00 | 00 | 00 |
| allergies | 1- | 1- | 01 | 01 | | parallel-letter-freq | 1- | 1- | 01 | 1- |
| bank-account | 1- | 01 | 01 | 1- | | perfect-numbers | 1- | 1- | 1- | 1- |
| binary-search-tree | 00 | 00 | 00 | 00 | | **phone-number** | 1- | 1- | 1- | 1- |
| circular-buffer | 00 | 1- | 1- | 1- | | queen-attack | 1- | 1- | 1- | 01 |
| clock | 01 | 1- | 00 | 00 | | robot-name | 01 | 00 | 1- | 1- |
| complex-numbers | 01 | 01 | 00 | 01 | | space-age | 1- | 00 | 1- | 1- |
| crypto-square | 00 | 00 | 00 | 00 | | spiral-matrix | 00 | 1- | 1- | 00 |
| diamond | 00 | 00 | 00 | 00 | | sublist | 00 | 00 | 00 | 1- |
| dnd-character | 00 | 1- | 00 | 01 | | yacht | 1- | 01 | 1- | 01 |
| gigasecond | 00 | 00 | 00 | 00 | | zebra-puzzle | 00 | 00 | 00 | 00 |
| grade-school | 1- | 1- | 1- | 1- | | kindergarten-garden | 00 | 00 | 00 | 00 |
| knapsack | 1- | 1- | 1- | 1- | | linked-list | 01 | 00 | 01 | 00 |

- Always pass@1 (4/4 trials): all-your-base, grade-school, knapsack,
  perfect-numbers, phone-number.
- Never passed in any trial (7): binary-search-tree, crypto-square, diamond,
  gigasecond, kindergarten-garden, meetup, zebra-puzzle.
- Conditional recovery: 16/59 first-turn failures fixed by turn 2 (27.1%),
  consistent with the release statistics.
- Only anomaly: trial 2's phone-number session logged one error output and
  one context exhaustion yet still passed on turn 0. Error/context-exhaustion
  pairs per trial: 20/14/12/11, always 1:1, and many such attempts passed.

## 6. Provenance and hash chain

Verified locally (byte-compared or re-hashed):

- All 12 files in `docs/worklogs/phone-number-iter14-gcs-audit/` pass
  `checksums.sha256`; local copies in `/tmp/phone_iter14_gcs_audit` are
  byte-identical.
- Data manifest SHA-256 `2c0e004d…d50c` matches the training gate, run
  receipt, and the eval archives; manifest `prompt_sha256` values re-hash
  correctly against all 8 train.jsonl rows.
- Hidden-test SHA-256 `5c13fb88…6e22` is constant on all 5,280 rollout rows
  and equals the SHA-256 of the packaged grader `test.cpp` (byte-identical
  across all 8 tasks).
- `verification_gate` string `phone-number-strange-12-independent-kernel-
  gcc13-v1` constant on all rows; source commit `0521ea26…98`.

Attested but not byte-verifiable:

- The four adapter weight files (iter-14 `62fa190a…575a`, iter-19
  `394b1b73…7bd6`): hashes recorded in the training gate and matched by the
  HF LFS upload and the eval receipts, but the 486 MB weight blobs were
  never re-hashed locally.
- Source adapter `c9afe1ed…d766` (lives outside this run's bucket).
- The 40 rollout PTs and the data JSONL/task files are not hash-bound
  anywhere (size/timestamp only in the inventory).
- `run.log` (13 MB) deliberately excluded from the artifact manifest as
  `sensitive_content`.

## 7. Conclusions

1. The release numbers are now fully substantiated. The Fixed26 archives
   exist, are bound to the scored adapter by SHA-256 at four independent
   points per trial, and reproduce pass@1 11.25/26 and pass@2 15.25/26
   exactly. The previous "summary-only" caveat is resolved.
2. Checkpoint selection was not evidence-based: training reward and pass
   rate peaked at update 9, and the only monitor was the training set
   itself (byte-identical files). Whether iter 9 would have scored higher
   on Fixed26 is unknown and testable.
3. The reward's "12 independent kernels" are at most 9 effective signals
   (two duplicate groups proven identical on 5,120/5,120 rows), and the
   PH-E03 characteristic IDs are mislabeled relative to the standalone
   verifier pack.
4. The dominant training weakness is structural repair (name-collision,
   missing-definitions, full-solve = 73.8% of failures), and 7 of 26
   Fixed26 tasks were never solved in any trial — consistent with the
   narrow-objective ceiling analysis, though per-task causality for the
   never-passed set remains unproven.
5. Training-side infrastructure was clean: zero timeouts, zero
   infrastructure errors, all status flags reconcile; the only logging gap
   is 120 rollout rows missing from W&B and `timing_status: unverified`.

## 8. Evidence index

- Training audit: `docs/worklogs/phone-number-iter14-gcs-audit/` (inventory,
  gate, receipts, per-update report + generator).
- Ceiling analysis: `docs/worklogs/checkpoint-11-25-ceiling/README.md`.
- Release README: `docs/worklogs/checkpoint-11-25-ceiling/README (2) (1).md`
  (duplicate of the staging release doc in
  `docs/worklogs/phone-number-iter14-release/`).
- Deep extraction outputs (session-local): `/tmp/phone_iter14_gcs_audit/
  deep_dive/` — `REPORT.md`, per-update×task CSVs, kernel-failure CSV,
  failure-reason stats, example rows, anomalies.
- Fixed26 recovery outputs (session-local):
  `/tmp/phone_iter14_fixed26_eval/` — four trial archives + `REPORT.md`.
- Primary stores: GCS
  `gs://skypilot-filemounts-ubuntu-f0048940-88p8zkcq/phone-number-kernel12-grpo20-spot-20260822-102653/`
  (training), `gs://lifeandhalf-24122025-w8-biayn/runs/glm47/evaluations/aider-fixed26/`
  (evaluations), HF `Terrano09/phone-number-kernel12-GRPO20` (public
  adapters + dataset), W&B `glm47-phone-number-dnd-grpo` (metrics/tables).
