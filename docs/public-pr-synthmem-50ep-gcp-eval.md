# SynthMem 50-epoch public-PR evaluation on GCP

> Historical lane: this document preserves the SynthMem-v3 procedure. The current
> SynthMem-v1 epoch-50 thinking-on lane is
> [public-pr-synthmem-v1-ep50-thinking-gcp-eval.md](public-pr-synthmem-v1-ep50-thinking-gcp-eval.md).
>

This lane evaluates the exact `SynthMem-v3-v1std-50ep` checkpoint. For the next controlled experiment, use `SUITE=fmtlib-compact-repair-bestof4`. It remains one evaluation task, generates up to four isolated candidates, gives each failing candidate at most one sanitized compiler-feedback repair turn, and stops at the first executable pass. The historical `fmtlib-demo`, `fmtlib-compiler-repair`, and three-task `full` lanes remain available as frozen ablations. The run uses one `a2-ultragpu-4g` VM with four full NVIDIA A100 80 GB GPUs and SGLang tensor parallelism 4.

This is diagnostic public-patch evaluation only. The PRs and their fixes are
public and may occur in model pretraining. Results are not clean generalization
evidence and these tasks must not become positive training data.

The evaluator performs four distinct checks:

1. build-time static validation of task format, prompt quality, code-probe
   quality, and content integrity;
2. build-time base-fail/reference-pass/plausible-wrong-fail oracle replay;
3. suite-specific Aider evaluation: the compact v4 suite uses fresh repository copies for seeds 1701–1704, disables Aider auto-lint and auto-test, uses diff editing at temperature 0.7, and gives a failed candidate one temperature-0.2 repair turn containing only the first sanitized editable-header compiler diagnostic;
4. post-attempt comparison of the model patch with the evaluator-only upstream
   production patch, plus deterministic failure classification and log evidence.

## Frozen identities

| Item | Exact identity |
| --- | --- |
| GCP machine type | `a2-ultragpu-4g` |
| GPU topology | 4× NVIDIA A100 80 GB, TP4 |
| DLVM family | `common-cu129-ubuntu-2204-nvidia-580` resolved to an exact image before VM creation |
| Base model revision | `7dd20894a642a0aa287e9827cb1a1f7f91386b67` |
| Training run | `glm47-synth-mem-v3-v1std-50ep-20260803T023833Z` |
| Source adapter SHA-256 | `5ca6a0cbede843e8c042ebb1004a80e85d85686974063cb9bd0540e236aab6ca` |
| Full task JSONL | `public-pr-repo-eval-v2-r5.jsonl` |
| Full task JSONL SHA-256 | `316e293ecf3a183b1f14612007e47edfbbea3e2b72ee5349b95b12d0a779ec82` |
| Demo task JSONL | `public-pr-repo-eval-demo-fmtlib-v2.jsonl` |
| Demo task JSONL SHA-256 | `9db4bbc4df06aed1cb87dca1026456f2cafa3973f15024fba41b3c912d5b22a7` |
| Compiler-repair task JSONL | `public-pr-repo-eval-demo-fmtlib-v3.jsonl` |
| Compiler-repair JSONL SHA-256 | `01d2015df04766726b778948997be9d34aa48cba1e78c002d92429b582e0765c` |
| Compact best-of-four JSONL | `public-pr-repo-eval-demo-fmtlib-v4.jsonl` |
| Compact best-of-four JSONL SHA-256 | `03ed4454a8953b80b09325392c0045e9ea0ba64b6c483ea886c3850ffbd7c7a3` |
| Compact final prompt SHA-256 | `c2e80dccbd50d0c9e1e38ba06a4c021821ac82fb16ba500ac0358a4fe5e9ced5` |
| Aider commit | `5dc9490bb35f9729ef2c95d00a19ccd30c26339c` |
| CMake | `3.27.9` |
| GCC | `13` |
| Compact candidate seeds | `1701`, `1702`, `1703`, `1704` |
| Sampling | temperature `0.7`, top-p `1.0`, maximum `32,768` completion tokens |

Google documents `a2-ultragpu-4g` as 48 vCPUs, 680 GB system memory,
four A100 80 GB GPUs, and 320 GB total GPU memory. A2 GPU VMs require
`--maintenance-policy=TERMINATE`. The selected current DLVM family uses CUDA
12.9 and NVIDIA driver 580. Resolve the family to an exact image name and keep
that name in the run receipt.

Official references:

- https://cloud.google.com/compute/docs/accelerator-optimized-machines
- https://cloud.google.com/compute/docs/gpus/create-gpu-vm-accelerator-optimized
- https://cloud.google.com/deep-learning-vm/docs/images
- https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

## 1. Set local GCP variables

Run these commands on the workstation with this checkout and authenticated
`gcloud`, `modal`, and GCS access:

```bash
export PROJECT_ID="YOUR_GCP_PROJECT"
export ZONE="us-central1-a"
export VM_NAME="glm47-synthmem-50ep-pr-eval"
export BUCKET="gs://YOUR_EVAL_BUCKET"
export GCP_ASSET_PREFIX="${BUCKET}/glm47-public-pr-eval/assets"
export GCP_RESULT_PREFIX="${BUCKET}/glm47-public-pr-eval/results"
export TRAINING_RUN="glm47-synth-mem-v3-v1std-50ep-20260803T023833Z"
export ADAPTER_REL="${TRAINING_RUN}/checkpoints/sft_lora_r16/iter_0001299/adapter"
```

Do not assume the example zone has capacity. List zones that publish the exact
machine type, choose one with quota/capacity, then update `ZONE`:

```bash
gcloud compute machine-types list \
  --project="${PROJECT_ID}" \
  --filter='name=a2-ultragpu-4g' \
  --format='table(zone.basename(),name,guestCpus,memoryMb)'

gcloud compute machine-types describe a2-ultragpu-4g \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"
```

## 2. Move the model and exact adapter from Modal to GCS

If the bytes already exist in GCS, verify their paths and skip the download.
Otherwise use a workstation with at least 80 GB free temporary space:

```bash
mkdir -p /tmp/glm47-gcp-assets/model /tmp/glm47-gcp-assets/adapter

modal volume get glm47-models \
  GLM-4.7-Flash \
  /tmp/glm47-gcp-assets/model

modal volume get glm47-runs \
  "${ADAPTER_REL}" \
  /tmp/glm47-gcp-assets/adapter

printf '%s\n' '7dd20894a642a0aa287e9827cb1a1f7f91386b67' \
  > /tmp/glm47-gcp-assets/model/.source-revision
printf '%s\n' "${TRAINING_RUN}" \
  > /tmp/glm47-gcp-assets/adapter/.training-run-id

(
  cd /tmp/glm47-gcp-assets/model
  find . -type f ! -name '.source-*' -print0 | LC_ALL=C sort -z | \
    xargs -0 sha256sum > .source-manifest.sha256
)
export MODEL_MANIFEST_SHA256="$(
  sha256sum /tmp/glm47-gcp-assets/model/.source-manifest.sha256 | awk '{print $1}'
)"
printf 'model manifest SHA-256: %s\n' "${MODEL_MANIFEST_SHA256}"

test "$(sha256sum /tmp/glm47-gcp-assets/adapter/adapter_model.bin | awk '{print $1}')" = \
  '5ca6a0cbede843e8c042ebb1004a80e85d85686974063cb9bd0540e236aab6ca'

export ADAPTER_CONFIG_SHA256="$(
  sha256sum /tmp/glm47-gcp-assets/adapter/adapter_config.json | awk '{print $1}'
)"
printf 'adapter_config SHA-256: %s\n' "${ADAPTER_CONFIG_SHA256}"

gcloud storage rsync --recursive \
  /tmp/glm47-gcp-assets/model \
  "${GCP_ASSET_PREFIX}/model/GLM-4.7-Flash"
gcloud storage rsync --recursive \
  /tmp/glm47-gcp-assets/adapter \
  "${GCP_ASSET_PREFIX}/adapter"
```

Preserve the printed adapter-config digest. The runtime requires it and records
it independently from the already frozen adapter-model digest.

## 3. Resolve an exact DLVM image and create the VM

```bash
export DLVM_FAMILY="common-cu129-ubuntu-2204-nvidia-580"
export DLVM_IMAGE="$(
  gcloud compute images describe-from-family "${DLVM_FAMILY}" \
    --project=deeplearning-platform-release \
    --format='value(name)'
)"
test -n "${DLVM_IMAGE}"
printf 'Resolved DLVM image: %s\n' "${DLVM_IMAGE}"

gcloud compute instances create "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --machine-type=a2-ultragpu-4g \
  --maintenance-policy=TERMINATE \
  --restart-on-failure \
  --image="${DLVM_IMAGE}" \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=500GB \
  --boot-disk-type=pd-ssd \
  --metadata=install-nvidia-driver=True \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

The A2 Ultra VM also receives 1.5 TB of Local SSD automatically. This runbook
uses the persistent boot disk so receipts survive a process failure. For higher
I/O throughput, mount the Local SSD as scratch only; do not keep the sole copy
of results there.

## 4. Upload the exact evaluator source bundle

From the repository root:

```bash
tar -czf /tmp/public-pr-gcp-bundle.tgz \
  configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl \
  configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl.sha256 \
  configs/public_pr_eval/private_probes \
  docker/public-pr-synthmem-gcp/Dockerfile \
  scripts/gcp_public_pr_eval_host_setup.sh \
  scripts/gcp_public_pr_eval_run.sh \
  scripts/gcp_public_pr_synthmem_50ep_eval.py \
  scripts/public_pr_repo_eval.py \
  scripts/validate_public_pr_eval.py \
  src/glm47_posttraining/public_pr_eval

gcloud compute scp /tmp/public-pr-gcp-bundle.tgz \
  "${VM_NAME}:/tmp/public-pr-gcp-bundle.tgz" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"
```

## 5. Prepare the VM and stage GCS assets

Connect to the VM:

```bash
gcloud compute ssh "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"
```

Then run on the VM:

```bash
export BUCKET="gs://YOUR_EVAL_BUCKET"
export GCP_ASSET_PREFIX="${BUCKET}/glm47-public-pr-eval/assets"
export GCP_RESULT_PREFIX="${BUCKET}/glm47-public-pr-eval/results"

sudo mkdir -p /opt/glm47-public-pr/{source,assets/model,assets/adapter,results}
sudo chown -R "${USER}:${USER}" /opt/glm47-public-pr
tar -xzf /tmp/public-pr-gcp-bundle.tgz -C /opt/glm47-public-pr/source
cd /opt/glm47-public-pr/source

sudo bash scripts/gcp_public_pr_eval_host_setup.sh

gcloud storage rsync --recursive \
  "${GCP_ASSET_PREFIX}/model/GLM-4.7-Flash" \
  /opt/glm47-public-pr/assets/model/GLM-4.7-Flash
gcloud storage rsync --recursive \
  "${GCP_ASSET_PREFIX}/adapter" \
  /opt/glm47-public-pr/assets/adapter

cat /opt/glm47-public-pr/assets/model/GLM-4.7-Flash/.source-revision
sha256sum /opt/glm47-public-pr/assets/model/GLM-4.7-Flash/.source-manifest.sha256
cat /opt/glm47-public-pr/assets/adapter/.training-run-id
sha256sum /opt/glm47-public-pr/assets/adapter/adapter_model.bin
sha256sum /opt/glm47-public-pr/assets/adapter/adapter_config.json
```

The host setup pins NVIDIA Container Toolkit `1.19.1-1`, configures Docker with
`nvidia-ctk`, and rejects any topology other than four full A100 80 GB GPUs.

## 6. Build and run the evaluation

Still on the VM, set the values recorded above. Use a new `RUN_ID` every time:

```bash
cd /opt/glm47-public-pr/source

export MODEL_DIR="/opt/glm47-public-pr/assets/model/GLM-4.7-Flash"
export MODEL_MANIFEST_SHA256="PASTE_THE_MODEL_MANIFEST_SHA256_FROM_STEP_2"
export ADAPTER_DIR="/opt/glm47-public-pr/assets/adapter"
export RESULT_DIR="/opt/glm47-public-pr/results"
export ADAPTER_CONFIG_SHA256="PASTE_THE_CONFIG_SHA256_FROM_STEP_2"
export IMAGE_NAME="glm47-public-pr-gcp:a100-r5-v4"
export RUN_ID="synthmem-v3-v1std-50ep-fmtlib-v4-$(date -u +%Y%m%dT%H%M%SZ)"
export SUITE="fmtlib-compact-repair-bestof4"
export GCP_PROJECT="YOUR_GCP_PROJECT"
export GCP_ZONE="YOUR_SELECTED_ZONE"
export GCP_INSTANCE="glm47-synthmem-50ep-pr-eval"
export GCP_DLVM_IMAGE="PASTE_THE_RESOLVED_EXACT_IMAGE_NAME"
export GCP_RESULT_PREFIX="gs://YOUR_EVAL_BUCKET/glm47-public-pr-eval/results"

bash scripts/gcp_public_pr_eval_run.sh 2>&1 | \
  tee "/opt/glm47-public-pr/results/${RUN_ID}.console.log"
```

`fmtlib-compact-repair-bestof4` is one evaluation task, not four tasks. Candidate 1/4 through 4/4 are independent solutions made from fresh prepared repositories. Attempt 1/2 is an initial edit; attempt 2/2 is an optional compiler-guided repair of that same candidate. The lane stops as soon as a candidate passes the complete executable oracle. If none passes, it retains the candidate that reached the furthest executable stage; reference similarity and textual checklist coverage never select the winner.

Aider auto-lint and auto-test are disabled only in this v4 lane so an opaque internal lint loop cannot rewrite the candidate. The evaluator remains authoritative: it applies the edit, performs scope checks, builds, runs the public chrono tests, executes the independent probe, and exposes at most the first sanitized editable-header compiler diagnostic. Aider can still make its own diff-format reflection calls, so model-call markers are recorded in each attempt receipt rather than assuming one model call per Aider invocation.

The Docker build uses network access to clone pinned evaluator repositories and
prefetch dependencies. It will fail unless the selected suite's base/reference/wrong oracle triples behave as required. The final `docker run` uses `--network none`;
the runtime additionally verifies that only the loopback interface exists.

Expected progress messages include:

- suite preparation task and command boundaries;
- 30-second heartbeats for long CMake builds;
- oracle replay results;
- adapter hashing/conversion;
- 30-second SGLang startup heartbeats;
- each Aider attempt and each build/test/probe stage;
- the final pass@1/pass@2 summary and report path.

## 7. Monitor without interrupting the run

Open a second SSH session:

```bash
watch -n 5 'nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv'
```

Inspect container status and the console log:

```bash
sudo docker ps --format 'table {{.ID}}\t{{.Image}}\t{{.Status}}'
tail -f "/opt/glm47-public-pr/results/${RUN_ID}.console.log"
```

Do not restart Docker while evaluation is running. NVIDIA documents a known
systemd-cgroup issue where a daemon reload can cause running containers to lose
GPU access.

## 8. Inspect and upload the results

```bash
export RUN_ROOT="/opt/glm47-public-pr/results/runs/${RUN_ID}"

cat "${RUN_ROOT}/evaluation/diagnostic-report.md"
jq '{run_id, training_run_id, gpu_inventory, suite: .suite | {pass_at_1,pass_at_2}}' \
  "${RUN_ROOT}/run-receipt.json"

find "${RUN_ROOT}/evaluation" -path '*attempt-*-diagnostics/diagnostics.md' \
  -print -exec sed -n '1,220p' {} \;

gcloud storage rsync --recursive \
  "${RUN_ROOT}" \
  "${GCP_RESULT_PREFIX}/${RUN_ID}"
```

Download from the workstation:

```bash
mkdir -p "artifacts/public_pr_eval/gcp/${RUN_ID}"
gcloud storage rsync --recursive \
  "${GCP_RESULT_PREFIX}/${RUN_ID}" \
  "artifacts/public_pr_eval/gcp/${RUN_ID}"
```

## 9. Reading the failure analysis

Every attempt contains:

- `attempt-N-aider.log`: raw Aider/model interaction;
- `attempt-N-score/score.json`: exact allowlist, build, test, and probe result;
- `attempt-N-diagnostics/candidate-production.patch`: model production patch;
- `attempt-N-diagnostics/upstream-reference.patch`: evaluator-only public PR patch;
- `attempt-N-diagnostics/candidate-vs-reference/*.diff`: line comparison;
- `attempt-N-diagnostics/failure-log-tail.txt`: final 8,000 characters of the
  first failed deterministic command;
- `attempt-N-diagnostics/diagnostics.json` and `.md`: structured and readable
  explanations.

Failure classes have these meanings:

| Class | Interpretation |
| --- | --- |
| `no_production_change` | The model did not edit the required production file. |
| `scope_violation` | It changed a path outside the exact allowlist. |
| `configure_failure` | The candidate broke repository configuration. |
| `compile_or_link_failure` | The repository or target failed to compile/link. |
| `regression_test_failure` | It compiled but failed the upstream regression suite. |
| `independent_probe_compile_failure` | The independent consumer/probe no longer compiles. |
| `independent_probe_runtime_failure` | Public tests passed but the separate behavioral probe failed. |
| `evaluator_inconsistency_reference_failed` | The candidate exactly matches the upstream production file but fails; treat this as evaluator/infrastructure failure, not model failure. |

An exact upstream-patch match is not required. A semantically different patch
passes when all executable checks pass. Conversely, high text similarity does
not override a deterministic failure.

## 10. Stop billing

After results are present in GCS:

```bash
gcloud compute instances stop "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}"
```

Delete the VM only after confirming that the result receipt, per-attempt logs,
patch comparisons, and diagnostic report have all been copied successfully.
