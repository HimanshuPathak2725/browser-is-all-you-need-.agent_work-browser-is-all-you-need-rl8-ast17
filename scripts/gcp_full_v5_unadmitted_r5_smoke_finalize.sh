#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
CERTIFIER="scripts/create_unadmitted_grpo_smoke_receipt.py"
RUN_ID="${1:?smoke run ID is required}"
RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-/opt/glm47-full-v5/results}"
RUN_ROOT="${RESULT_ROOT}/runs/${RUN_ID}"
RECOVERED_ROOT="${RESULT_ROOT}/gcs-recovery/${RUN_ID}"
GCS_RUN="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/unadmitted-smoke-r5-thinking-final-resp16384-pack18432-v1/${RUN_ID}"
SMOKE_RECEIPT="${RUN_ROOT}/smoke-gate-receipt.json"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TRAIN_IMAGE="glm47-full-v5-unadmitted-grpo:gcp-r5-thinking-final-resp16384-pack18432-v1"

if ! [[ "${RUN_ID}" =~ ^unadmitted-r5-smoke-[A-Za-z0-9][A-Za-z0-9._-]{0,143}$ ]]; then
  echo "invalid R5 smoke run ID: ${RUN_ID}" >&2
  exit 2
fi
if [[ -e "${RECOVERED_ROOT}" ]]; then
  echo "refusing to reuse GCS recovery path: ${RECOVERED_ROOT}" >&2
  exit 2
fi

cd "${REPO_ROOT}"
"${PYTHON_BIN}" "${DRIVER}" train \
  --phase experimental \
  --run-id "${RUN_ID}" \
  --result-root "${RESULT_ROOT}"

mkdir -p "${RECOVERED_ROOT}/checkpoints/grpo_lora_r16"
gcloud storage rsync --recursive --checksums-only \
  "${GCS_RUN}/checkpoints/grpo_lora_r16" \
  "${RECOVERED_ROOT}/checkpoints/grpo_lora_r16"

if docker info >/dev/null 2>&1; then
  DOCKER=(docker)
else
  DOCKER=(sudo docker)
fi
TRAIN_IMAGE_ID="$("${DOCKER[@]}" image inspect --format='{{.Id}}' "${TRAIN_IMAGE}")"
if ! [[ "${TRAIN_IMAGE_ID}" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "smoke trainer image has no immutable Docker ID" >&2
  exit 2
fi

"${DOCKER[@]}" run --rm --network none \
  --volume "${RESULT_ROOT}:${RESULT_ROOT}" \
  --volume "${REPO_ROOT}/${CERTIFIER}:/opt/smoke-certifier.py:ro" \
  "${TRAIN_IMAGE_ID}" \
  python3 /opt/smoke-certifier.py \
  --run-id "${RUN_ID}" \
  --run-root "${RUN_ROOT}" \
  --recovered-root "${RECOVERED_ROOT}" \
  --output "${SMOKE_RECEIPT}" \
  --expected-profile-id "aider-full-v5-experimental-unadmitted-r5-thinking-final-resp16384-pack18432-v1-smoke" \
  --run-id-prefix "unadmitted-r5-smoke-" \
  --permit-field "permits_r5_57_update_launch"

gcloud storage cp \
  "${SMOKE_RECEIPT}" \
  "${GCS_RUN}/smoke-gate-receipt.json"

echo "SMOKE_GATE_RECEIPT=${SMOKE_RECEIPT}"
echo "SMOKE_GATE_GCS=${GCS_RUN}/smoke-gate-receipt.json"
