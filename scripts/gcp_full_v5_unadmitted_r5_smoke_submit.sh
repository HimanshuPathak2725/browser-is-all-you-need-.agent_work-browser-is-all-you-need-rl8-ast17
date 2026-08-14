#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
PROJECT="lifeandhalf-24122025"
ZONE="us-central1-a"
INSTANCE="glm47-full-v5-charm-h100-8"
REMOTE_ROOT_BASE="browser-is-all-you-need-staging"
AUTH_ENV="GLM47_FULL_V5_UNADMITTED_SMOKE_AUTHORIZATION"
AUTH_PHRASE="I_AUTHORIZE_UNADMITTED_R5_ONE_UPDATE_SMOKE_AND_GCP_COSTS"
RUN_ID="${1:-unadmitted-r5-smoke-$(date -u +%Y%m%dT%H%M%SZ)}"
REMOTE_ROOT="${REMOTE_ROOT_BASE}/${RUN_ID}-stage-$(date -u +%Y%m%dT%H%M%SZ)-$$"
SOURCE_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
HASH_INPUTS=(
  scripts/gcp_full_v5_charm_grpo.py
  scripts/gcp_full_v5_unadmitted_r5_smoke_headless.sh
  scripts/gcp_full_v5_unadmitted_r5_smoke_finalize.sh
  scripts/create_unadmitted_grpo_smoke_receipt.py
  scripts/train_grpo.sh
  scripts/check_runtime.py
  scripts/prepare_grpo_adapter.py
  scripts/convert_checkpoint.sh
  scripts/publish_results.py
  configs/full_v5_charm_grpo/gcp-r1.json
  configs/full_v5_charm_grpo/gcp-r5-unadmitted-thinking-final-resp16384-pack18432-v1-smoke.json
  docker/full-v5-charm-grpo-gcp/Dockerfile
  docker/full-v5-charm-grpo-gcp/Verifier.Dockerfile
  examples/grpo.sh
  src/glm47_posttraining/__init__.py
  src/glm47_posttraining/constants.py
  src/glm47_posttraining/aider_polyglot
  src/glm47_posttraining/cpp_perf
  src/glm47_posttraining/integrations
)

if ! [[ "${RUN_ID}" =~ ^unadmitted-r5-smoke-[A-Za-z0-9][A-Za-z0-9._-]{0,143}$ ]]; then
  echo "run ID must begin with unadmitted-r5-smoke- and contain only safe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must explicitly authorize the unadmitted one-update GCP smoke" >&2
  exit 2
fi
if ! [[ "${SOURCE_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "local source commit is not a lowercase 40-character Git SHA" >&2
  exit 2
fi
for path in "${HASH_INPUTS[@]}"; do
  if [[ ! -e "${REPO_ROOT}/${path}" ]]; then
    echo "missing required staged build input: ${path}" >&2
    exit 2
  fi
done

status="$(gcloud compute instances describe "${INSTANCE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --format='value(status)')"
case "${status}" in
  RUNNING) ;;
  TERMINATED)
    gcloud compute instances start "${INSTANCE}" \
      --project="${PROJECT}" \
      --zone="${ZONE}"
    ;;
  *)
    echo "VM is in unsupported state: ${status}" >&2
    exit 2
    ;;
esac

for _attempt in {1..60}; do
  status="$(gcloud compute instances describe "${INSTANCE}" \
    --project="${PROJECT}" \
    --zone="${ZONE}" \
    --format='value(status)')"
  [[ "${status}" == "RUNNING" ]] && break
  sleep 5
done
if [[ "${status}" != "RUNNING" ]]; then
  echo "VM did not reach RUNNING state" >&2
  exit 2
fi

gcloud compute ssh "${INSTANCE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --command="mkdir -p \
    ~/${REMOTE_ROOT}/scripts \
    ~/${REMOTE_ROOT}/configs/full_v5_charm_grpo \
    ~/${REMOTE_ROOT}/docker/full-v5-charm-grpo-gcp \
    ~/${REMOTE_ROOT}/examples \
    ~/${REMOTE_ROOT}/src/glm47_posttraining"

gcloud compute scp \
  "${REPO_ROOT}/scripts/gcp_full_v5_charm_grpo.py" \
  "${REPO_ROOT}/scripts/gcp_full_v5_unadmitted_r5_smoke_headless.sh" \
  "${REPO_ROOT}/scripts/gcp_full_v5_unadmitted_r5_smoke_finalize.sh" \
  "${REPO_ROOT}/scripts/create_unadmitted_grpo_smoke_receipt.py" \
  "${REPO_ROOT}/scripts/train_grpo.sh" \
  "${REPO_ROOT}/scripts/check_runtime.py" \
  "${REPO_ROOT}/scripts/prepare_grpo_adapter.py" \
  "${REPO_ROOT}/scripts/convert_checkpoint.sh" \
  "${REPO_ROOT}/scripts/publish_results.py" \
  "${INSTANCE}:~/${REMOTE_ROOT}/scripts/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp \
  "${REPO_ROOT}/configs/full_v5_charm_grpo/gcp-r1.json" \
  "${REPO_ROOT}/configs/full_v5_charm_grpo/gcp-r5-unadmitted-thinking-final-resp16384-pack18432-v1-smoke.json" \
  "${INSTANCE}:~/${REMOTE_ROOT}/configs/full_v5_charm_grpo/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp \
  "${REPO_ROOT}/docker/full-v5-charm-grpo-gcp/Dockerfile" \
  "${REPO_ROOT}/docker/full-v5-charm-grpo-gcp/Verifier.Dockerfile" \
  "${INSTANCE}:~/${REMOTE_ROOT}/docker/full-v5-charm-grpo-gcp/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp \
  "${REPO_ROOT}/examples/grpo.sh" \
  "${INSTANCE}:~/${REMOTE_ROOT}/examples/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp \
  "${REPO_ROOT}/src/glm47_posttraining/__init__.py" \
  "${REPO_ROOT}/src/glm47_posttraining/constants.py" \
  "${INSTANCE}:~/${REMOTE_ROOT}/src/glm47_posttraining/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp --recurse \
  "${REPO_ROOT}/src/glm47_posttraining/aider_polyglot" \
  "${REPO_ROOT}/src/glm47_posttraining/cpp_perf" \
  "${REPO_ROOT}/src/glm47_posttraining/integrations" \
  "${INSTANCE}:~/${REMOTE_ROOT}/src/glm47_posttraining/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"

local_hashes="$(
  cd "${REPO_ROOT}"
  LC_ALL=C find "${HASH_INPUTS[@]}" -type f -print0 \
    | LC_ALL=C sort -z \
    | xargs -0 sha256sum \
    | sha256sum
)"
local_hashes="${local_hashes%%[[:space:]]*}"
remote_hashes="$(gcloud compute ssh "${INSTANCE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --command="cd ~/${REMOTE_ROOT} && LC_ALL=C find ${HASH_INPUTS[*]} -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum")"
remote_hashes="${remote_hashes%%[[:space:]]*}"
if [[ "${local_hashes}" != "${remote_hashes}" ]]; then
  echo "remote staged build-context hash does not match local bytes: local=${local_hashes} remote=${remote_hashes}" >&2
  exit 2
fi

gcloud compute ssh "${INSTANCE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --command="cd ~/${REMOTE_ROOT} && GLM47_SOURCE_COMMIT=${SOURCE_COMMIT} ${AUTH_ENV}=${AUTH_PHRASE} bash scripts/gcp_full_v5_unadmitted_r5_smoke_headless.sh ${RUN_ID}"
