#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
CONFIG_REL="${GLM47_UNADMITTED_CONFIG_REL:-configs/full_v5_charm_grpo/gcp-r2-unadmitted-experiment.json}"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
AUTH_ENV="GLM47_FULL_V5_UNADMITTED_EXPERIMENT_AUTHORIZATION"
AUTH_PHRASE="I_AUTHORIZE_UNADMITTED_R2_57_UPDATE_EXPERIMENT_AND_GCP_COSTS"
RUN_ID="${1:-unadmitted-r2-$(date -u +%Y%m%dT%H%M%SZ)}"
RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-${HOME}/glm47-full-v5-local-results}"
CONTROL_ROOT="${RESULT_ROOT}/headless-control/${RUN_ID}"
LOG_PATH="${CONTROL_ROOT}/tmux-driver.log"
PID_PATH="${CONTROL_ROOT}/tmux-pane.pid"
TMUX_SESSION="grpo-${RUN_ID}"
GCS_ROOT="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/experiments/unadmitted-full-v5-r2"

if ! [[ "${RUN_ID}" =~ ^unadmitted-r2-[A-Za-z0-9][A-Za-z0-9._-]{0,143}$ ]]; then
  echo "run ID must begin with unadmitted-r2- and contain only safe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must authorize the unadmitted 57-update experiment" >&2
  exit 2
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required" >&2
  exit 2
fi
if [[ ! -f "${REPO_ROOT}/${CONFIG_REL}" || ! -f "${REPO_ROOT}/${DRIVER}" ]]; then
  echo "experimental driver or config is missing" >&2
  exit 2
fi
if tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
  echo "tmux session already exists: ${TMUX_SESSION}" >&2
  exit 2
fi

umask 077
mkdir -p "${CONTROL_ROOT}"
if [[ -e "${LOG_PATH}" || -e "${PID_PATH}" ]]; then
  echo "refusing to reuse control path: ${CONTROL_ROOT}" >&2
  exit 2
fi

PYTHON_BIN="python3"
[[ -x "${REPO_ROOT}/.venv-gcp/bin/python" ]] && PYTHON_BIN="${REPO_ROOT}/.venv-gcp/bin/python"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
export GLM47_FULL_V5_CONFIG_PATH="${REPO_ROOT}/${CONFIG_REL}"

cd "${REPO_ROOT}"
"${PYTHON_BIN}" "${DRIVER}" inspect >"${CONTROL_ROOT}/inspect.json"
"${PYTHON_BIN}" "${DRIVER}" render --phase experimental --run-id "${RUN_ID}" >"${CONTROL_ROOT}/render.json"
"${PYTHON_BIN}" "${DRIVER}" host-check >"${CONTROL_ROOT}/host-check.log" 2>&1
"${PYTHON_BIN}" "${DRIVER}" prepare --result-root "${RESULT_ROOT}" --receipt "${CONTROL_ROOT}/preparation-receipt.json" >"${CONTROL_ROOT}/prepare.log" 2>&1
sha256sum "${DRIVER}" "${CONFIG_REL}" "${BASH_SOURCE[0]}" >"${CONTROL_ROOT}/CONTROL_SHA256SUMS"

printf -v TRAIN_COMMAND 'cd %q && exec %q %q train --phase experimental --run-id %q --result-root %q >>%q 2>&1' "${REPO_ROOT}" "${PYTHON_BIN}" "${DRIVER}" "${RUN_ID}" "${RESULT_ROOT}" "${LOG_PATH}"
tmux new-session -d -s "${TMUX_SESSION}" "${TRAIN_COMMAND}"
sleep 2
if ! tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
  echo "tmux session exited during startup" >&2
  tail -80 "${LOG_PATH}" >&2 || true
  exit 2
fi
tmux display-message -p -t "${TMUX_SESSION}" '#{pane_pid}' >"${PID_PATH}"
gcloud storage cp --recursive "${CONTROL_ROOT}" "${GCS_ROOT}/control/" >/dev/null

echo "HEADLESS_RUN_ID=${RUN_ID}"
echo "TMUX_SESSION=${TMUX_SESSION}"
echo "HEADLESS_LOG=${LOG_PATH}"
echo "RESULT_GCS_PREFIX=${GCS_ROOT}/${RUN_ID}"
echo "MONITOR_TMUX=tmux attach -t ${TMUX_SESSION}"
echo "MONITOR_LOG=tail -F ${LOG_PATH}"

if [[ "${GLM47_HEADLESS_WAIT:-0}" == "1" ]]; then
  while tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; do sleep 30; done
  RECEIPT="${RESULT_ROOT}/runs/${RUN_ID}/execution-receipt.json"
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); raise SystemExit(0 if p.get("status") == "passed" else 2)' "${RECEIPT}"
fi
