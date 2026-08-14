#!/usr/bin/env bash
set -euo pipefail

MODE="${GLM47_SKYPILOT_MODE:-smoke}"
RUN_ID="${RUN_ID:-}"
CONFIG_REL="configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87-skypilot.json"
LOCAL_RESULT_ROOT="${GLM47_FULL_V5_RESULT_ROOT:-${HOME}/glm47-full-v5-local-results}"
DURABLE_RESULT_ROOT="${GLM47_FULL_V5_DURABLE_RESULT_ROOT:-${HOME}/glm47-results-store/runs/glm47/charm/r7-admitted-mef-exact40-r87}"
DRIVER="scripts/gcp_full_v5_charm_grpo.py"
FULL_AUTH_ENV="GLM47_CHARM_R7_FULL_TRAINING_AUTHORIZATION"
FULL_AUTH_PHRASE="I_AUTHORIZE_CHARM_R7_ADMITTED_MEF_EXACT40_FULL_TRAINING_AND_GCP_COSTS"

if ! [[ "${RUN_ID}" =~ ^charm-r7-r87-[A-Za-z0-9][A-Za-z0-9._-]{0,143}$ ]]; then
  echo "RUN_ID must begin with charm-r7-r87- and contain only safe characters" >&2
  exit 2
fi
if [[ "${MODE}" != "smoke" && "${MODE}" != "canary" && "${MODE}" != "full" ]]; then
  echo "GLM47_SKYPILOT_MODE must be smoke, canary, or full" >&2
  exit 2
fi

require_value() {
  local variable_name="$1"
  if [[ -z "${!variable_name:-}" ]]; then
    echo "${variable_name} is required for R7 ${MODE}" >&2
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

if [[ "${MODE}" == "canary" ]]; then
  require_value PRETRAINING_RECEIPT_GCS_URI
  require_sha256 PRETRAINING_RECEIPT_SHA256
  require_value CANARY_TASK_MANIFEST_GCS_URI
  require_sha256 CANARY_TASK_MANIFEST_SHA256
elif [[ "${MODE}" == "full" ]]; then
  require_value PROMOTION_RECEIPT_GCS_URI
  require_sha256 PROMOTION_RECEIPT_SHA256
  if [[ "${!FULL_AUTH_ENV:-}" != "${FULL_AUTH_PHRASE}" ]]; then
    echo "${FULL_AUTH_ENV} must explicitly authorize the promoted full R7 run and GCP costs" >&2
    exit 2
  fi
fi

export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"
export GLM47_FULL_V5_CONFIG_PATH="${CONFIG_REL}"
export GLM47_PROVISIONER="skypilot"
export GLM47_EXECUTION_PROFILE="gcp-skypilot-h100-tp4-ep8-dp8-admitted-r7-mef-r87"

mkdir -p "${LOCAL_RESULT_ROOT}/preparations/${RUN_ID}"
mkdir -p "${DURABLE_RESULT_ROOT}/preparations/${RUN_ID}"

python3 "${DRIVER}" host-check

ADMISSION_ROOT="${LOCAL_RESULT_ROOT}/admission/${RUN_ID}"
mkdir -p "${ADMISSION_ROOT}"

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

PRETRAINING_RECEIPT="${ADMISSION_ROOT}/pre-training.json"
CANARY_TASK_MANIFEST="${ADMISSION_ROOT}/canary-task-manifest.json"
PROMOTION_RECEIPT="${ADMISSION_ROOT}/promotion.json"

if [[ "${MODE}" == "canary" ]]; then
  download_gcs_file "${PRETRAINING_RECEIPT_GCS_URI}" "${PRETRAINING_RECEIPT}"
  download_gcs_file "${CANARY_TASK_MANIFEST_GCS_URI}" "${CANARY_TASK_MANIFEST}"
  printf '%s  %s\n' "${PRETRAINING_RECEIPT_SHA256}" "${PRETRAINING_RECEIPT}" | sha256sum --check --status
  printf '%s  %s\n' "${CANARY_TASK_MANIFEST_SHA256}" "${CANARY_TASK_MANIFEST}" | sha256sum --check --status
elif [[ "${MODE}" == "full" ]]; then
  download_gcs_file "${PROMOTION_RECEIPT_GCS_URI}" "${PROMOTION_RECEIPT}"
  printf '%s  %s\n' "${PROMOTION_RECEIPT_SHA256}" "${PROMOTION_RECEIPT}" | sha256sum --check --status
fi

PREPARATION_RECEIPT="${LOCAL_RESULT_ROOT}/preparations/${RUN_ID}/preparation-receipt.json"
python3 "${DRIVER}" prepare \
  --result-root "${LOCAL_RESULT_ROOT}" \
  --receipt "${PREPARATION_RECEIPT}"

cp "${PREPARATION_RECEIPT}" \
  "${DURABLE_RESULT_ROOT}/preparations/${RUN_ID}/preparation-receipt.json"

if [[ "${MODE}" == "smoke" ]]; then
  echo "CHARM_R7_SKYPILOT_SMOKE=passed"
  echo "PREPARATION_RECEIPT=${PREPARATION_RECEIPT}"
  exit 0
fi

if [[ "${MODE}" == "canary" ]]; then
  python3 "${DRIVER}" train \
    --phase canary \
    --run-id "${RUN_ID}" \
    --result-root "${LOCAL_RESULT_ROOT}" \
    --pretraining-receipt "${PRETRAINING_RECEIPT}" \
    --expected-pretraining-sha256 "${PRETRAINING_RECEIPT_SHA256}" \
    --canary-task-manifest "${CANARY_TASK_MANIFEST}" \
    --expected-canary-task-manifest-sha256 "${CANARY_TASK_MANIFEST_SHA256}"
else
  python3 "${DRIVER}" train \
    --phase full \
    --run-id "${RUN_ID}" \
    --result-root "${LOCAL_RESULT_ROOT}" \
    --promotion-receipt "${PROMOTION_RECEIPT}" \
    --expected-promotion-sha256 "${PROMOTION_RECEIPT_SHA256}"
fi
