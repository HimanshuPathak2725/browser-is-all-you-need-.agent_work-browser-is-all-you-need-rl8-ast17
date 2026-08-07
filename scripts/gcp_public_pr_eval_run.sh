#!/usr/bin/env bash
set -euo pipefail

: "${MODEL_DIR:?set MODEL_DIR to the staged GLM-4.7-Flash directory}"
: "${MODEL_MANIFEST_SHA256:?set the .source-manifest.sha256 digest}"
: "${ADAPTER_DIR:?set ADAPTER_DIR to the staged 50-epoch adapter directory}"
: "${RESULT_DIR:?set RESULT_DIR to a persistent result directory}"
: "${ADAPTER_CONFIG_SHA256:?set the adapter_config.json SHA-256}"
: "${RUN_ID:?set a new unique evaluation run ID}"
: "${GCP_PROJECT:?set the GCP project ID for the receipt}"
: "${GCP_ZONE:?set the exact GCP zone for the receipt}"
: "${GCP_INSTANCE:?set the GCP instance name for the receipt}"
: "${GCP_DLVM_IMAGE:?set the resolved exact DLVM image name for the receipt}"

IMAGE_NAME="${IMAGE_NAME:-glm47-public-pr-gcp:a100-r1}"
SUITE="${SUITE:-fmtlib-demo}"

test -f "${MODEL_DIR}/.source-revision"
test -f "${ADAPTER_DIR}/.training-run-id"
mkdir -p "${RESULT_DIR}"

sudo docker build --progress=plain \
  --file docker/public-pr-synthmem-gcp/Dockerfile \
  --tag "${IMAGE_NAME}" \
  .
EVAL_IMAGE_ID="$(sudo docker image inspect --format '{{.Id}}' "${IMAGE_NAME}")"

sudo docker run --rm \
  --gpus all \
  --network none \
  --ipc host \
  --shm-size 128g \
  --env "GCP_PROJECT=${GCP_PROJECT}" \
  --env "GCP_ZONE=${GCP_ZONE}" \
  --env "GCP_INSTANCE=${GCP_INSTANCE}" \
  --env "GCP_MACHINE_TYPE=a2-ultragpu-4g" \
  --env "GCP_DLVM_IMAGE=${GCP_DLVM_IMAGE}" \
  --env "EVAL_IMAGE_ID=${EVAL_IMAGE_ID}" \
  --volume "${MODEL_DIR}:/models/GLM-4.7-Flash:ro" \
  --volume "${ADAPTER_DIR}:/adapter:ro" \
  --volume "${RESULT_DIR}:/results" \
  "${IMAGE_NAME}" \
  --model-path /models/GLM-4.7-Flash \
  --expected-model-manifest-sha256 "${MODEL_MANIFEST_SHA256}" \
  --adapter-path /adapter \
  --expected-adapter-config-sha256 "${ADAPTER_CONFIG_SHA256}" \
  --output-root /results \
  --run-id "${RUN_ID}" \
  --suite "${SUITE}"

echo "Suite: ${SUITE}"
echo "Result: ${RESULT_DIR}/runs/${RUN_ID}/run-receipt.json"
echo "Diagnosis: ${RESULT_DIR}/runs/${RUN_ID}/evaluation/diagnostic-report.md"
