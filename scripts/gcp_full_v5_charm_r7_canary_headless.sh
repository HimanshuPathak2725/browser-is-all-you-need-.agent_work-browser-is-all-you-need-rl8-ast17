#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
CONFIG_REL="configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87.json"
CANARY_REL="configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-canary.json"
PRETRAINING_REL="artifacts/charm-task-generation-v1/v1r87-20260812T122334Z/remediation-004/v1-pretraining-admission-receipt-v011.json"
RUNTIME_SUBDIR="runtime/charm-r7-admitted-mef-exact40-r87-20260812T190000Z"
RUNTIME_TREE_SHA256="88a65fc1dae1909d33e1053fd4fe8f8493a45a3c3968ec7b68fea1afc0826dca"
PRETRAINING_SHA256="f129fb2c953e7c87fae3f796c9c04c546943f0ad8518c0cfc795a85c1c4218e0"
CANARY_SHA256="5308b5a260d8a4dd467cfe833298f47b6c05ecb04047f0d114e052a36410cf67"
AUTH_ENV="GLM47_CHARM_R7_CANARY_AUTHORIZATION"
AUTH_PHRASE="I_AUTHORIZE_CHARM_R7_ADMITTED_MEF_EXACT40_CANARY_AND_GCP_COSTS"
RUN_ID="${1:-charm-r7-r87-canary-$(date -u +%Y%m%dT%H%M%SZ)}"
RUNTIME_ARCHIVE_REL="${2:-}"
RUNTIME_ARCHIVE_SHA256="${3:-}"
RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-/opt/glm47-full-v5/results}"
ASSET_ROOT="${GLM47_FULL_V5_ASSET_ROOT:-/opt/glm47-full-v5/assets}"
RUNTIME_ROOT="${ASSET_ROOT}/${RUNTIME_SUBDIR}"
CONTROL_ROOT="${RESULT_ROOT}/headless-control/${RUN_ID}"
LOG_PATH="${CONTROL_ROOT}/headless-driver.log"
PID_PATH="${CONTROL_ROOT}/driver.pid"
TMUX_PATH="${CONTROL_ROOT}/tmux-session.txt"
TMUX_SESSION="grpo-${RUN_ID}"
GCS_ROOT="gs://lifeandhalf-24122025-w8-biayn/runs/glm47/charm/r7-admitted-mef-exact40-r87"

if ! [[ "${RUN_ID}" =~ ^charm-r7-r87-canary-[A-Za-z0-9][A-Za-z0-9._-]{0,132}$ ]]; then
  echo "run ID must begin with charm-r7-r87-canary- and contain only safe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must explicitly authorize this admitted 8xH100 canary and its GCP costs" >&2
  exit 2
fi
if [[ -z "${RUNTIME_ARCHIVE_REL}" || ! -f "${REPO_ROOT}/${RUNTIME_ARCHIVE_REL}" ]]; then
  echo "staged R7 runtime archive is missing" >&2
  exit 2
fi
if ! [[ "${RUNTIME_ARCHIVE_SHA256}" =~ ^[0-9a-f]{64}$ ]]; then
  echo "runtime archive SHA-256 is invalid" >&2
  exit 2
fi
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is required for the persistent canary" >&2
  exit 2
fi

for required in "${DRIVER}" "${CONFIG_REL}" "${CANARY_REL}" "${PRETRAINING_REL}"; do
  if [[ ! -f "${REPO_ROOT}/${required}" ]]; then
    echo "missing staged canary input: ${required}" >&2
    exit 2
  fi
done
printf '%s  %s\n' "${RUNTIME_ARCHIVE_SHA256}" "${REPO_ROOT}/${RUNTIME_ARCHIVE_REL}" | sha256sum --check --status
printf '%s  %s\n' "${PRETRAINING_SHA256}" "${REPO_ROOT}/${PRETRAINING_REL}" | sha256sum --check --status
printf '%s  %s\n' "${CANARY_SHA256}" "${REPO_ROOT}/${CANARY_REL}" | sha256sum --check --status

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
export GLM47_FULL_V5_ASSET_ROOT="${ASSET_ROOT}"

sudo mkdir -p "${ASSET_ROOT}/runtime"
if [[ -d "${RUNTIME_ROOT}" ]]; then
  sudo chown -R "$(id -u):$(id -g)" "${RUNTIME_ROOT}"
  existing_runtime_tree="$(${PYTHON_BIN} -c 'import sys; from pathlib import Path; from glm47_posttraining.aider_polyglot.charm_grpo import tree_sha256; print(tree_sha256(Path(sys.argv[1])))' "${RUNTIME_ROOT}")"
  if [[ "${existing_runtime_tree}" != "${RUNTIME_TREE_SHA256}" ]]; then
    quarantine_root="${RUNTIME_ROOT}.stale-${RUN_ID}"
    if [[ -e "${quarantine_root}" ]]; then
      echo "refusing to reuse stale-runtime quarantine path: ${quarantine_root}" >&2
      exit 2
    fi
    sudo mv -- "${RUNTIME_ROOT}" "${quarantine_root}"
  fi
fi
if [[ ! -d "${RUNTIME_ROOT}" ]]; then
  sudo tar -xzf "${REPO_ROOT}/${RUNTIME_ARCHIVE_REL}" -C "${ASSET_ROOT}/runtime"
fi
sudo chown -R "$(id -u):$(id -g)" "${RUNTIME_ROOT}"
actual_runtime_tree="$(${PYTHON_BIN} -c 'import sys; from pathlib import Path; from glm47_posttraining.aider_polyglot.charm_grpo import tree_sha256; print(tree_sha256(Path(sys.argv[1])))' "${RUNTIME_ROOT}")"
if [[ "${actual_runtime_tree}" != "${RUNTIME_TREE_SHA256}" ]]; then
  echo "R7 runtime tree mismatch after staging: expected=${RUNTIME_TREE_SHA256} actual=${actual_runtime_tree}" >&2
  exit 2
fi

cd "${REPO_ROOT}"
"${PYTHON_BIN}" "${DRIVER}" inspect >"${CONTROL_ROOT}/inspect.json"
"${PYTHON_BIN}" "${DRIVER}" render \
  --phase canary \
  --run-id "${RUN_ID}" >"${CONTROL_ROOT}/render.json"
"${PYTHON_BIN}" "${DRIVER}" host-check >"${CONTROL_ROOT}/host-check.log" 2>&1
"${PYTHON_BIN}" "${DRIVER}" prepare \
  --result-root "${RESULT_ROOT}" \
  --receipt "${CONTROL_ROOT}/preparation-receipt.json" \
  >"${CONTROL_ROOT}/prepare.log" 2>&1

sha256sum \
  "${DRIVER}" \
  "${CONFIG_REL}" \
  "${CANARY_REL}" \
  "${PRETRAINING_REL}" \
  scripts/train_grpo.sh \
  >"${CONTROL_ROOT}/CONTROL_SHA256SUMS"
printf '%s\n' "${RUNTIME_TREE_SHA256}" >"${CONTROL_ROOT}/RUNTIME_TREE_SHA256"

TRAIN_ARGS=(
  train
  --phase canary
  --run-id "${RUN_ID}"
  --result-root "${RESULT_ROOT}"
  --pretraining-receipt "${REPO_ROOT}/${PRETRAINING_REL}"
  --expected-pretraining-sha256 "${PRETRAINING_SHA256}"
  --canary-task-manifest "${REPO_ROOT}/${CANARY_REL}"
  --expected-canary-task-manifest-sha256 "${CANARY_SHA256}"
)
printf -v TMUX_COMMAND '%q ' "${PYTHON_BIN}" "${DRIVER}" "${TRAIN_ARGS[@]}"
TMUX_COMMAND+=">$(printf '%q' "${LOG_PATH}") 2>&1"
tmux new-session -d -s "${TMUX_SESSION}" -c "${REPO_ROOT}" "${TMUX_COMMAND}"
DRIVER_PID="$(tmux list-panes -t "${TMUX_SESSION}" -F '#{pane_pid}' | head -1)"
printf '%s\n' "${DRIVER_PID}" >"${PID_PATH}"
printf '%s\n' "${TMUX_SESSION}" >"${TMUX_PATH}"

sleep 2
if ! tmux has-session -t "${TMUX_SESSION}" 2>/dev/null; then
  echo "tmux canary driver exited during startup; inspect ${LOG_PATH}" >&2
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
