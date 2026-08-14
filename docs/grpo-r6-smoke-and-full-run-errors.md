# R6 GRPO Smoke and Full-Run Error Summary

## Purpose

This document summarizes the confirmed failures and successful results observed
during the recent R3-R6 GRPO smoke and full-run attempts. It distinguishes
resource fixes, reward-verifier failures, signal-gate failures, full-corpus
failures, and successful optimizer execution.

## Current outcome at a glance

| Area | Current outcome | Meaning |
| --- | --- | --- |
| GPU memory | Addressed for the tested reduced limits | The 16,384-token response limit ran at approximately 69-73 GB instead of exhausting an 80 GB H100. |
| One-update smoke | Passed | At least one optimizer update completed with the reduced memory profile. |
| Hybrid45 task compatibility | Addressed by dataset restriction | Training was restricted to 475 `aider_cpp17` tasks that can expose the required executable checks. |
| Hidden-check instrumentation | Addressed for the next smoke | Instrumentation was updated after helper-style tests reported zero independent checks. |
| Original 50% format gate | Failed | Only 39% of 200 responses used the exact whole-file format, so the optimizer update was correctly blocked. |
| Duplicate task groups | Bypassed by policy relaxation | Strict unique-group enforcement was disabled, but the underlying sampler behavior was not corrected. |
| Complete-corpus verifier stability | Unresolved | The full run still aborts on the concurrency-related verifier infrastructure path. |
| Reduced 40-task execution | Passed | Six optimizer updates and six signal gates completed on a selected non-concurrent subset. |
| Complete 475-task run | Not completed | No successful full-corpus optimizer run has been demonstrated yet. |

## Detailed confirmed errors and results

| Stage | Confirmed error or result | Impact | Current status |
| --- | --- | --- | --- |
| R3 smoke | CUDA out of memory at 80,175 MiB | Ray workers terminated before training could begin. | Addressed by reducing the maximum response length and packed-token limit. |
| R4 smoke | CUDA out of memory at 80,989 MiB | Reducing dynamic packing alone was insufficient to fit the workload. | Addressed in the later R5/R6 configuration. Recent successful attempts used approximately 69-73 GB. |
| R5 smoke | One optimizer update passed with a 69,385 MiB peak | Demonstrated that the reduced 16,384-token response limit fits on the available H100 memory. | Passed for the one-update smoke scope. This does not by itself establish full-corpus stability. |
| R6 task preparation | `official_cmake` tasks did not expose five independently executable hidden partitions | Hybrid45 could not produce its required five hidden functional outcomes for those tasks. | Addressed by restricting the training dataset to 475 compatible `aider_cpp17` tasks. |
| R6 verifier instrumentation | Hidden-grader instrumentation detected zero independent checks for helper-style tests | Evaluation of `pcr-camera-frames` aborted before a usable reward could be produced. | Instrumentation was updated, and the following smoke progressed beyond this failure point. |
| R6 signal-gate smoke | Exact whole-file format rate was 39%, below the required 50% | The signal gate stopped the run before the optimizer update. Only 78 of 200 responses parsed, although 75 of those 78 parsed responses compiled. | Remains a failed smoke under the original 50% policy. Passing after lowering the threshold must be reported as a policy change, not as improvement under the original gate. |
| First full attempt | Aider rollout contained duplicate task groups | The run stopped before any optimizer update. | The retry disabled strict unique-group enforcement. This bypassed the check but did not fix the sampler or establish independence between logical task groups. |
| Full-run retry | Numeric reward was refused after a verifier infrastructure failure on `aider-cpp-rl/concurrent-tag-factory` | The full run again stopped before any optimizer update. The failure was not converted into a model-quality reward. | Unresolved for the complete corpus. The failure appears associated with the concurrency/TSan path, but detailed low-level evidence was unavailable because verifier logs were disabled. |
| Reduced 40-task run | Six optimizer updates completed and all six signal gates passed | Demonstrated that training, reward execution, signal validation, optimization, and checkpointing work on the selected non-concurrent subset. | Passed with a 73,339 MiB peak. Exact-format rates were 53.1-70%, and compile rates among parsed responses were 95.4-100%. |

## Failure progression

| Phase | Blocking condition | Change made | What the next run proved |
| --- | --- | --- | --- |
| R3 | 80,175 MiB CUDA OOM | Reduced response and packed-token limits | Memory pressure was lowered, but the first adjustment was not yet sufficient. |
| R4 | 80,989 MiB CUDA OOM | Further R5/R6 memory-profile reduction | The subsequent one-update run fit within H100 memory. |
| R5 | No memory failure | Retained the 16,384 response limit | One optimizer update completed at 69,385 MiB. |
| R6 preparation | Incompatible task harnesses | Restricted the corpus to 475 `aider_cpp17` tasks | Hybrid45 could operate on the selected harness family. |
| R6 instrumentation | Zero discovered independent checks | Updated hidden-check instrumentation | The following smoke progressed to the rollout signal gate. |
| R6 smoke | 39% exact-format rate against a 50% requirement | Later configuration lowered the threshold | The original smoke remains failed; lowering the rule does not retroactively pass it. |
| First full run | Duplicate logical task groups | Disabled strict unique-group enforcement | The retry moved past this guard without correcting sampler behavior. |
| Full retry | Concurrency verifier infrastructure failure | No complete fix yet | The complete 475-task corpus remains unverified. |
| Reduced run | No blocking failure across selected tasks | Used a non-concurrent 40-task subset | Six optimizer updates passed, proving the reduced path only. |

## Interpretation of the successful evidence

The recent runs establish the following:

- The reduced token profile fits within the available H100 memory.
- Ray, SGLang, reward workers, signal gating, optimization, and checkpointing can
  complete multiple updates together.
- Hybrid45 works on the selected compatible and non-concurrent task subset.
- Parsed responses usually compile: the reduced run observed a 95.4-100%
  compile rate among responses that satisfied the whole-file parser.
- Exact-format output remains an important bottleneck because compilation is
  only evaluated after parsing succeeds.

The recent runs do not yet establish the following:

- Successful execution over all 475 selected tasks.
- A corrected unique logical-task sampler.
- Stable concurrency/TSan verification for the complete task set.
- A pass under the original 50% format threshold for the failed 39% smoke.
- Training admission, checkpoint promotion, or deployment readiness.

## Current blocker hierarchy

| Priority | Blocker | Why it matters | Completion condition |
| ---: | --- | --- | --- |
| 1 | Concurrency verifier infrastructure failure | It prevents the complete corpus from reaching an optimizer update. | Preserve the low-level failure, repair the verifier path, and rerun the affected task successfully under the same safety contract. |
| 2 | Duplicate logical-task grouping | Relaxing enforcement can hide correlated or repeated groups in a GRPO batch. | Implement and verify a variant-aware sampler or enforce unique logical tasks per optimizer update. |
| 3 | Format-rate policy and behavior | The model failed the original 50% requirement, while a lower threshold changes the acceptance policy. | Freeze one justified threshold and report model improvement separately from threshold changes. |
| 4 | Full-corpus evidence | The six-update success covers only a curated 40-task subset. | Complete a new smoke and planned run using the full 475-task schedule. |

## System flow and observed stop points

```text
Prompt schedule ------> rollout generation ------> whole-file parsing ------> compilation and Hybrid45 verification ------> rollout signal gate ------> optimizer update ------> checkpoint publication
```

```text
R3/R4 ------> CUDA OOM before training
R5 ------> one optimizer update passed
R6 smoke ------> format gate stopped before optimizer
First full run ------> duplicate-group gate stopped before optimizer
Full retry ------> verifier infrastructure failure stopped before optimizer
Reduced 40-task run ------> six signal gates passed ------> six optimizer updates completed
```

## Current overall status

The GRPO pipeline is operational on the tested reduced, non-concurrent subset.
The full 475-task path is still incomplete because duplicate-group handling was
relaxed rather than repaired and the concurrency verifier failure remains
unresolved. The reduced run is positive engineering evidence, but it is not a
full-corpus pass or an admission result.
