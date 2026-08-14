#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
CONFIG_REL="configs/full_v5_charm_grpo/gcp-r2-unadmitted-experiment.json"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
AUTH_ENV="GLM47_FULL_V5_UNADMITTED_EXPERIMENT_AUTHORIZATION"
AUTH_PHRASE="I_AUTHORIZE_UNADMITTED_R2_57_UPDATE_EXPERIMENT_AND_GCP_COSTS"
RUN_ID="${1:-unadmitted-r2-$(date -u +%Y%m%dT%H%M%SZ)}"
RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-/opt/glm47-full-v5/results}"
CONTROL_ROOT="${RESULT_ROOT}/headless-control/${RUN_ID}"
LOG_PATH="${CONTROL_ROOT}/headless-driver.log"
PID_PATH="${CONTROL_ROOT}/driver.pid"
GCS_ROOT="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/unadmitted-full-v5-r2"

if ! [[ "${RUN_ID}" =~ ^unadmitted-r2-[A-Za-z0-9][A-Za-z0-9._-]{0,143}$ ]]; then
  echo "run ID must begin with unadmitted-r2- and contain only safe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must explicitly authorize the unadmitted 57-update GCP experiment" >&2
  exit 2
fi
if [[ ! -f "${REPO_ROOT}/${CONFIG_REL}" || ! -f "${REPO_ROOT}/${DRIVER}" ]]; then
  echo "experimental driver or config is missing from ${REPO_ROOT}" >&2
  exit 2
fi

umask 077
mkdir -p "${CONTROL_ROOT}"
if [[ -e "${PID_PATH}" || -e "${LOG_PATH}" ]]; then
  echo "refusing to reuse headless control path: ${CONTROL_ROOT}" >&2
  exit 2
fi

if [[ -x "${REPO_ROOT}/.venv-gcp/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.venv-gcp/bin/python"
elif [[ -x "/home/ubuntu/browser-is-all-you-need/.venv-gcp/bin/python" ]]; then
  PYTHON_BIN="/home/ubuntu/browser-is-all-you-need/.venv-gcp/bin/python"
else
  PYTHON_BIN="python3"
fi

export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export GLM47_FULL_V5_CONFIG_PATH="${REPO_ROOT}/${CONFIG_REL}"

cd "${REPO_ROOT}"
"${PYTHON_BIN}" "${DRIVER}" inspect >"${CONTROL_ROOT}/inspect.json"
"${PYTHON_BIN}" "${DRIVER}" render \
  --phase experimental \
  --run-id "${RUN_ID}" >"${CONTROL_ROOT}/render.json"
"${PYTHON_BIN}" "${DRIVER}" host-check >"${CONTROL_ROOT}/host-check.log" 2>&1
"${PYTHON_BIN}" "${DRIVER}" prepare \
  --result-root "${RESULT_ROOT}" \
  --receipt "${CONTROL_ROOT}/preparation-receipt.json" \
  >"${CONTROL_ROOT}/prepare.log" 2>&1

sha256sum \
  "${DRIVER}" \
  "${CONFIG_REL}" \
  "scripts/train_grpo.sh" \
  >"${CONTROL_ROOT}/CONTROL_SHA256SUMS"

nohup "${PYTHON_BIN}" "${DRIVER}" train \
  --phase experimental \
  --run-id "${RUN_ID}" \
  --result-root "${RESULT_ROOT}" \
  >"${LOG_PATH}" 2>&1 </dev/null &
DRIVER_PID=$!
printf '%s\n' "${DRIVER_PID}" >"${PID_PATH}"

sleep 2
if ! kill -0 "${DRIVER_PID}" 2>/dev/null; then
  echo "headless driver exited during startup; inspect ${LOG_PATH}" >&2
  tail -80 "${LOG_PATH}" >&2 || true
  exit 2
fi

gcloud storage cp --recursive "${CONTROL_ROOT}" "${GCS_ROOT}/control/" >/dev/null

echo "HEADLESS_RUN_ID=${RUN_ID}"
echo "HEADLESS_DRIVER_PID=${DRIVER_PID}"
echo "HEADLESS_LOG=${LOG_PATH}"
echo "RESULT_GCS_PREFIX=${GCS_ROOT}/${RUN_ID}"
echo "MONITOR=tail -F ${LOG_PATH}"
