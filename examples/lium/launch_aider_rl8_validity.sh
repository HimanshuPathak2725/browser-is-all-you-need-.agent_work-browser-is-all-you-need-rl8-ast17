#!/usr/bin/env bash
set -euo pipefail

repo_root="${GLM47_REPRO_REPO_ROOT:-/workspace/glm47}"
source_commit="${GLM47_REPRO_SOURCE_COMMIT:?set GLM47_REPRO_SOURCE_COMMIT to the committed training revision}"
runtime_image="${GLM47_REPRO_RUNTIME_IMAGE:-glm47-fixed:${source_commit:0:12}}"
run_id="${GLM47_REPRO_RUN_ID:-glm47-aider-rl8-validity-$(date -u +%Y%m%dT%H%M%SZ)}"
source_adapter="${GLM47_REPRO_SOURCE_ADAPTER:-/workspace/assets/sft-v3-r16-clean}"
base_model="${GLM47_REPRO_MODEL_PATH:-/workspace/models/GLM-4.7-Flash}"
reference_checkpoint="${GLM47_REPRO_REF_LOAD_DIR:-/workspace/models/GLM-4.7-Flash_torch_dist_tp4_pp1_ep8}"
docker_cli="$(command -v docker)"
launch_log="/workspace/logs/${run_id}.container.log"
status_log="/workspace/logs/${run_id}.status"

if [[ "$(git -C "${repo_root}" rev-parse HEAD)" != "${source_commit}" ]]; then
  echo "source commit mismatch in ${repo_root}" >&2
  exit 2
fi
if [[ -n "$(git -C "${repo_root}" status --porcelain)" ]]; then
  echo "training checkout is dirty: ${repo_root}" >&2
  exit 2
fi
if [[ ! -f /workspace/hf_token || "$(stat -c '%a' /workspace/hf_token)" != 600 ]]; then
  echo "missing mode-0600 Hugging Face token file" >&2
  exit 2
fi
for path in "${source_adapter}/adapter_model.bin" "${source_adapter}/adapter_config.json" \
  "${base_model}/config.json" "${reference_checkpoint}/latest_checkpointed_iteration.txt"; do
  if [[ ! -f "${path}" ]]; then
    echo "missing launch input: ${path}" >&2
    exit 2
  fi
done
if [[ -e "/workspace/runs/${run_id}" || -e "/workspace/runs/${run_id}-preservation" ]]; then
  echo "refusing to reuse run outputs for ${run_id}" >&2
  exit 2
fi
if docker inspect "${run_id}" >/dev/null 2>&1; then
  echo "container already exists: ${run_id}" >&2
  exit 2
fi

mkdir -p /workspace/logs /workspace/tmp
runtime_image_id="$(docker image inspect "${runtime_image}" --format '{{.Id}}')"
sandbox_image_id="$(docker image inspect glm47-aider-polyglot-cpp:latest --format '{{.Id}}')"

container_id="$(docker run -d \
  --name "${run_id}" \
  --gpus all \
  --ipc host \
  --network host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  -v /workspace:/workspace \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "${docker_cli}:/usr/bin/docker:ro" \
  -e TMPDIR=/workspace/tmp \
  -e TMP=/workspace/tmp \
  -e TEMP=/workspace/tmp \
  -e GLM47_REPRO_RUN_ID="${run_id}" \
  -e GLM47_REPRO_REPO_ROOT="${repo_root}" \
  -e GLM47_REPRO_ASSETS_ROOT=/workspace/assets \
  -e GLM47_REPRO_RUNS_ROOT=/workspace/runs \
  -e GLM47_REPRO_MODEL_PATH="${base_model}" \
  -e GLM47_REPRO_REF_LOAD_DIR="${reference_checkpoint}" \
  -e GLM47_REPRO_SOURCE_ADAPTER="${source_adapter}" \
  -e WANDB_MODE=offline \
  "${runtime_image}" \
  bash -lc "cd '${repo_root}' && exec bash examples/lium/aider_rl8_validity.sh")"

nohup docker logs -f "${run_id}" >"${launch_log}" 2>&1 &
echo "$!" >"${launch_log}.pid"
nohup bash -c '
  set -u
  container="$1"
  status_file="$2"
  while [[ "$(docker inspect -f "{{.State.Running}}" "${container}" 2>/dev/null || true)" == true ]]; do
    sleep 15
  done
  docker inspect -f "exit_code={{.State.ExitCode}} finished_at={{.State.FinishedAt}} oom={{.State.OOMKilled}} error={{json .State.Error}}" "${container}" >"${status_file}" 2>&1
' _ "${run_id}" "${status_log}" >/dev/null 2>&1 &
echo "$!" >"${status_log}.watcher.pid"

echo "run_id=${run_id}"
echo "container_id=${container_id}"
echo "runtime_image=${runtime_image}"
echo "runtime_image_id=${runtime_image_id}"
echo "sandbox_image_id=${sandbox_image_id}"
echo "container_log=${launch_log}"
echo "status_log=${status_log}"
