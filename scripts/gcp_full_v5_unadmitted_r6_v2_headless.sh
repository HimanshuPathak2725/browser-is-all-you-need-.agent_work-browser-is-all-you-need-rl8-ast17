#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
BYPASS_ENV="GLM47_R6_V2_SMOKE_BYPASS_AUTHORIZATION"
BYPASS_PHRASE="I_AUTHORIZE_R6_V2_SMOKE_GATE_BYPASS_AFTER_FAILED_EXACT_FORMAT_SMOKE"
RUN_ID="${1:-unadmitted-r6-v2-full-$(date -u +%Y%m%dT%H%M%SZ)}"
SMOKE_RECEIPT_REL="${2:-}"
SMOKE_RECEIPT_SHA256="${3:-}"
RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-/opt/glm47-full-v5/results}"
CONTROL_ROOT="${RESULT_ROOT}/headless-control/${RUN_ID}"
LOG_PATH="${CONTROL_ROOT}/headless-driver.log"
PID_PATH="${CONTROL_ROOT}/driver.pid"
TMUX_PATH="${CONTROL_ROOT}/tmux-session.txt"
TMUX_SESSION="grpo-${RUN_ID}"

case "${RUN_ID}" in
  unadmitted-r6-v2-four-topic40-*)
    CONFIG_REL="configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-four-topic40.json"
    AUTH_ENV="GLM47_FULL_V5_HYBRID45_V2_FOUR_TOPIC40_EXPERIMENT_AUTHORIZATION"
    AUTH_PHRASE="I_AUTHORIZE_UNADMITTED_R6_HYBRID45_V2_FOUR_TOPIC40_6_UPDATE_EXPERIMENT_AND_GCP_COSTS"
    GCS_ROOT="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/unadmitted-r6-hybrid45-v2-four-topic40"
    ;;
  unadmitted-r6-v2-full-*)
    CONFIG_REL="configs/full_v5_charm_grpo/gcp-r6-hybrid45-v2-full.json"
    AUTH_ENV="GLM47_FULL_V5_HYBRID45_V2_EXPERIMENT_AUTHORIZATION"
    AUTH_PHRASE="I_AUTHORIZE_UNADMITTED_R6_HYBRID45_V2_57_UPDATE_EXPERIMENT_AND_GCP_COSTS"
    GCS_ROOT="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/unadmitted-r6-hybrid45-v2-full"
    ;;
  *)
    echo "run ID must use an R6 V2 full or four-topic40 prefix" >&2
    exit 2
    ;;
esac
if ! [[ "${RUN_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$ ]]; then
  echo "run ID contains unsafe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must explicitly authorize the unadmitted R6 V2 57-update GCP experiment" >&2
  exit 2
fi
if [[ "${!BYPASS_ENV:-}" == "${BYPASS_PHRASE}" ]]; then
  BYPASS_MODE=1
else
  BYPASS_MODE=0
fi
if [[ ! -f "${REPO_ROOT}/${CONFIG_REL}" || ! -f "${REPO_ROOT}/${DRIVER}" ]]; then
  echo "experimental driver or config is missing from ${REPO_ROOT}" >&2
  exit 2
fi
if [[ "${BYPASS_MODE}" -eq 0 ]] && { [[ ! -f "${REPO_ROOT}/${SMOKE_RECEIPT_REL}" ]] || ! [[ "${SMOKE_RECEIPT_SHA256}" =~ ^[0-9a-f]{64}$ ]]; }; then
  echo "smoke PASS receipt or its SHA-256 is invalid" >&2
  exit 2
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required for the persistent headless run" >&2
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

CONTROL_INPUTS=("${DRIVER}" "${CONFIG_REL}" "scripts/train_grpo.sh")
if [[ "${BYPASS_MODE}" -eq 0 ]]; then
  CONTROL_INPUTS+=("${SMOKE_RECEIPT_REL}")
fi
sha256sum "${CONTROL_INPUTS[@]}" >"${CONTROL_ROOT}/CONTROL_SHA256SUMS"

TRAIN_ARGS=(
  train
  --phase experimental
  --run-id "${RUN_ID}"
  --result-root "${RESULT_ROOT}"
)
if [[ "${BYPASS_MODE}" -eq 0 ]]; then
  TRAIN_ARGS+=(
    --smoke-receipt "${REPO_ROOT}/${SMOKE_RECEIPT_REL}"
    --expected-smoke-receipt-sha256 "${SMOKE_RECEIPT_SHA256}"
  )
fi
printf -v TMUX_COMMAND '%q ' "${PYTHON_BIN}" "${DRIVER}" "${TRAIN_ARGS[@]}"
TMUX_COMMAND+=">$(printf '%q' "${LOG_PATH}") 2>&1"
tmux new-session -d -s "${TMUX_SESSION}" -c "${REPO_ROOT}" "${TMUX_COMMAND}"
DRIVER_PID="$(tmux list-panes -t "${TMUX_SESSION}" -F '#{pane_pid}' | head -1)"
printf '%s\n' "${DRIVER_PID}" >"${PID_PATH}"
printf '%s\n' "${TMUX_SESSION}" >"${TMUX_PATH}"

sleep 2
if ! tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
  echo "tmux driver exited during startup; inspect ${LOG_PATH}" >&2
  tail -80 "${LOG_PATH}" >&2 || true
  exit 2
fi

gcloud storage cp --recursive "${CONTROL_ROOT}" "${GCS_ROOT}/control/" >/dev/null

echo "HEADLESS_RUN_ID=${RUN_ID}"
echo "HEADLESS_DRIVER_PID=${DRIVER_PID}"
echo "TMUX_SESSION=${TMUX_SESSION}"
echo "HEADLESS_LOG=${LOG_PATH}"
echo "RESULT_GCS_PREFIX=${GCS_ROOT}/${RUN_ID}"
echo "MONITOR=tail -F ${LOG_PATH}"
echo "ATTACH=tmux attach -t ${TMUX_SESSION}"
