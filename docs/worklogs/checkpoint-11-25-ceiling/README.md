# Why the evaluated checkpoint has not shown a result above 11.25/26: verified evidence so far

The local run-summary note reports that the Phone Number GRPO20 `iter_0000014` checkpoint produced Fixed26 pass@1 scores of `11`, `12`, `11`, and `11`, giving a mean of `11.25/26`. The training run, checkpoint identity, adapter digest, and training-side measurements are verified below; the four Fixed26 scores remain summary-level evidence until their row-level archives are recovered.

This report does not claim that one verifier defect caused the reported score or that `11.25` is a model-capacity ceiling. It records only the limitations demonstrated by the available artifacts and keeps their possible effect on the 26-task evaluation explicitly unverified.

| Component or category | Role or failure pattern | Evidence or current status | How to verify | Files, controls, or next action |
|---|---|---|---|---|
| Narrow training objective | The checkpoint learned eight variants of one Phone Number task while Fixed26 measures 26 different tasks. | **Verified.** The training gate records `training_task_count=8`; every rollout row belongs to Phone Number. | Inspect the training gate and rollout task IDs. | Add balanced multi-topic data only after each dataset is aligned with its semantic verifier. |
| No independent checkpoint-selection eval | Training monitoring reused the same eight Phone variants and hidden test, so it could not measure cross-task generalization or reliably select the best Fixed26 checkpoint. | **Verified.** Dataset validation count is zero, the monitor is Phone-only, and the receipt records `post_update_eval=absent`. | Inspect the data manifest, run receipt, and 160 monitor rows. | Use a held-out multi-topic monitor that is separate from the training episodes and Fixed26 test rows. |
| Incomplete mastery of structural repair | Exact API/build/completeness tasks remained the dominant Phone training weakness. | **Verified.** Name-collision, missing-definition, and full-solve episodes produced `1,650/2,235` failures (`73.8%`). Their pass rates were only `46/640`, `82/640`, and `142/640`. | Recompute per-task results from the 5,120 normalized training rows. | Measure the same characteristic on the missing Fixed26 rows before claiming cross-task impact. |
| Non-monotonic optimization | More Phone updates did not produce continuous improvement even on the training objective. | **Verified.** Strict training pass rate peaked at update 9 (`157/256`, `61.33%`), was `151/256` (`58.98%`) at update 14, and ended at `144/256` (`56.25%`) at update 19. | Inspect the per-update report. | Evaluate every saved checkpoint on the same held-out selection set; do not select by training update number. |
| Policy-to-kernel misalignment | Training kernel IDs imply standalone verifier characteristics that the hidden reward does not actually execute. | **Verified in code.** Standalone `PH-E03` means authenticated official assets/build/tests; training `PH-E03-A/B/C` instead check selected valid inputs, formatting, and invalid inputs. | Compare the standalone PH-E03 policy with `HIDDEN_TEST_SOURCE`. | Give training kernels truthful characteristic IDs and run the authenticated official terminal policy separately. |
| Correlated and duplicated reward | Repeated behaviors receive several equal rewards, overweighting narrow Phone semantics without adding independent coverage. | **Verified in all 5,120 rows.** `PH-E02-A`, `PH-E03-A`, and `PH-E04-B` always agreed; `PH-E01-A` and `PH-E04-A` also always agreed. | Recompute pairwise kernel agreement from `kernel_bits`. | De-duplicate probes or aggregate first by C1-C10 characteristic and then weight characteristics. |
| Coarse compile-failure attribution | A build failure is converted into twelve failed semantic kernels, so GRPO and later analysis cannot identify which characteristic was actually responsible. | **Verified in code and rows.** When no receipt exists after a failed evaluation, the adapter substitutes `000000000000`; 130 failed training rows had compile errors. | Inspect `_apply_kernel_reward` and compile-failure records. | Score build/API failure separately and mark unexecuted semantic kernels `not-run`. |
| Missing general-purpose coverage | Several C1-C10 characteristics are absent from this Phone reward; their effect on Fixed26 is not yet measured. | **Verified from configuration/code.** C4 header/dependency/ODR is validated separately but inactive; the actual official C5 suite is absent from GRPO reward; dedicated C8 safety and C9 portability signals are absent. | Map every active reward kernel to the C1-C10 taxonomy. | Measure candidate coverage before proposing activation of task-owned probes. |
| Weak transfer measurement | The internal Phone monitor can show curriculum progress but cannot explain which non-Phone tasks block the mean. | **Verified boundary.** It contains `160` Phone rows, not four trials x 26 Fixed26 rows. | Locate and audit the four external eval archives. | Produce a per-task Fixed26 failure and regression matrix when those archives are available. |

## Directly verified facts

- The evaluated checkpoint is `phone-number-kernel12-grpo20-spot-20260822-102653/iter_0000014`, adapter SHA-256 `62fa190ad26e30fc1b5dd9543936ef549a49dd8cfa8220e4af726a1d499e575a`.
- The local run-summary note reports Fixed26 pass@1 values `11/26`, `12/26`, `11/26`, and `11/26`, for a four-run mean of `11.25/26`.
- Phone training passed `2,885/5,120` rows (`56.35%`) and failed `2,235/5,120`.
- The curriculum was balanced at `640` samples for each of its eight Phone episodes, so the structural failure dominance was not caused by sampling those episodes more often.
- Training had zero timeout and zero infrastructure failures; infrastructure instability is not supported as the main explanation.

## What the evidence establishes

The checkpoint was optimized on eight variants of one Phone contract, several reward kernels were empirically duplicate, and the internal monitor did not measure 26-task generalization. Structural repair remained the dominant Phone training failure family, and Phone training performance peaked before the selected update. These are verified properties of the run; the missing Fixed26 rows prevent proving how much each property contributed to the reported `11.25/26` mean.

## What is not yet proven

- The four Fixed26 scores currently come from a local summary, not independently reproduced task-level archives.
- Without those `4 x 26 = 104` task-trial rows, no specific missed Fixed26 task can be causally assigned to one Phone kernel, dataset row, or verifier characteristic.
- The evidence does not prove that `11.25` is a hard ceiling; one of the four trials already reached `12/26`.
- The categories above overlap. In particular, policy misalignment, reward duplication, and narrow coverage describe related aspects of the same reward design and must not be added as independent failure counts.

## Conclusion

The dominant verified mismatch is between the narrow Phone-only training objective and the broad 26-task target, combined with duplicate reward signals and no independent multi-topic selection monitor. The available evidence does **not** prove that this mismatch caused the reported mean or that `11.25/26` is a hard ceiling. The next decisive check is to recover the four eval archives, replay all 104 task-trial rows, and map each failure to the C1-C10 characteristic that was missing, mislabeled, or not learned.

## Evidence

- [Phone GRPO GCS audit](../phone-number-iter14-gcs-audit/README.md)
- [Per-update failure report](../phone-number-iter14-gcs-audit/per_update_failure_report.md)
- [Run receipt](../phone-number-iter14-gcs-audit/run_receipt.txt)
- [Training gate](../phone-number-iter14-gcs-audit/grpo_training_gate.json)
- [Common verifier characteristics](../../../Reward_GRPO/COMMON_VERIFIER_CHARACTERISTICS_REPORT.md)
- [Phone GRPO reward implementation](../../../Reward_GRPO/phone_number_grpo.py)
- [Standalone PH-E03 policy](<../../../Reward_GRPO/Phone_Number Verifiers/Verifier implementation policy/policy_03_official_functional_behavior.md>)
