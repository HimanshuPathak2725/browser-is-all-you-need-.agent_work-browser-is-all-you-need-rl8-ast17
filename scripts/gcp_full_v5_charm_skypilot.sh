#!/usr/bin/env bash
set -euo pipefail

MODE="${GLM47_SKYPILOT_MODE:-smoke}"
RUN_ID="${RUN_ID:-}"
LOCAL_RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-${HOME}/glm47-full-v5-local-results}"
DURABLE_RESULT_ROOT="${GLM47_FULL_V5_DURABLE_RESULT_ROOT:-${HOME}/glm47-full-v5-results}"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"

if ! [[ "${RUN_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$ ]]; then
  echo "RUN_ID must be a non-empty safe identifier" >&2
  exit 2
fi
if [[ "${MODE}" != "smoke" && "${MODE}" != "canary" ]]; then
  echo "GLM47_SKYPILOT_MODE must be smoke or canary; full training is not exposed here" >&2
  exit 2
fi

export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"
export GLM47_PROVISIONER="skypilot"
export GLM47_EXECUTION_PROFILE="gcp-skypilot-h100-tp4-ep8-dp8"

mkdir -p "${LOCAL_RESULT_ROOT}/preparations/${RUN_ID}"
mkdir -p "${DURABLE_RESULT_ROOT}/preparations/${RUN_ID}"

python3 "${DRIVER}" host-check

PREPARATION_RECEIPT="${LOCAL_RESULT_ROOT}/preparations/${RUN_ID}/preparation-receipt.json"
python3 "${DRIVER}" prepare \
  --result-root "${LOCAL_RESULT_ROOT}" \
  --receipt "${PREPARATION_RECEIPT}"

cp "${PREPARATION_RECEIPT}" \
  "${DURABLE_RESULT_ROOT}/preparations/${RUN_ID}/preparation-receipt.json"

if [[ "${MODE}" == "smoke" ]]; then
  echo "FULL_V5_CHARM_SKYPILOT_SMOKE=passed"
  echo "PREPARATION_RECEIPT=${PREPARATION_RECEIPT}"
  exit 0
fi

require_value() {
  local variable_name="$1"
  if [[ -z "${!variable_name:-}" ]]; then
    echo "${variable_name} is required for the CHARM canary" >&2
    exit 2
  fi
}

require_sha256() {
  local variable_name="$1"
  require_value "${variable_name}"
  if ! [[ "${!variable_name}" =~ ^[0-9a-f]{64}$ ]]; then
    echo "${variable_name} must be a lowercase SHA-256 digest" >&2
    exit 2
  fi
}

require_value PRETRAINING_RECEIPT_GCS_URI
require_sha256 PRETRAINING_RECEIPT_SHA256
require_value CANARY_TASK_MANIFEST_GCS_URI
require_sha256 CANARY_TASK_MANIFEST_SHA256

ADMISSION_ROOT="${LOCAL_RESULT_ROOT}/admission/${RUN_ID}"
mkdir -p "${ADMISSION_ROOT}"
PRETRAINING_RECEIPT="${ADMISSION_ROOT}/pre-training.json"
CANARY_TASK_MANIFEST="${ADMISSION_ROOT}/canary-task-manifest.json"

download_gcs_file() {
  local source_uri="$1"
  local destination="$2"
  if [[ "${source_uri}" != gs://* ]]; then
    echo "Admission artifacts must use immutable gs:// URIs" >&2
    exit 2
  fi
  if command -v gcloud >/dev/null 2>&1; then
    gcloud storage cp "${source_uri}" "${destination}"
  elif command -v gsutil >/dev/null 2>&1; then
    gsutil cp "${source_uri}" "${destination}"
  else
    echo "gcloud or gsutil is required to fetch admission artifacts" >&2
    exit 2
  fi
}

download_gcs_file "${PRETRAINING_RECEIPT_GCS_URI}" "${PRETRAINING_RECEIPT}"
download_gcs_file "${CANARY_TASK_MANIFEST_GCS_URI}" "${CANARY_TASK_MANIFEST}"

python3 "${DRIVER}" train \
  --phase canary \
  --run-id "${RUN_ID}" \
  --result-root "${LOCAL_RESULT_ROOT}" \
  --pretraining-receipt "${PRETRAINING_RECEIPT}" \
  --expected-pretraining-sha256 "${PRETRAINING_RECEIPT_SHA256}" \
  --canary-task-manifest "${CANARY_TASK_MANIFEST}" \
  --expected-canary-task-manifest-sha256 "${CANARY_TASK_MANIFEST_SHA256}"
