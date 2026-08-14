#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." &>/dev/null && pwd)"
PROJECT="lifeandhalf-24122025"
ZONE="us-central1-a"
INSTANCE="glm47-full-v5-charm-h100-8"
REMOTE_ROOT_BASE="browser-is-all-you-need-staging"
CONFIG_REL="configs/full_v5_charm_grpo/gcp-r7-admitted-mef-exact40-r87.json"
CANARY_REL="configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-canary.json"
SELECTION_REL="configs/full_v5_charm_grpo/r7-admitted-mef-exact40-r87-selection.json"
PRETRAINING_REL="artifacts/charm-task-generation-v1/v1r87-20260812T122334Z/remediation-004/v1-pretraining-admission-receipt-v011.json"
RUNTIME_REL="artifacts/charm-r7-admitted-mef-exact40-r87-20260812T190000Z"
RUNTIME_DIRNAME="charm-r7-admitted-mef-exact40-r87-20260812T190000Z"
RUNTIME_TREE_SHA256="88a65fc1dae1909d33e1053fd4fe8f8493a45a3c3968ec7b68fea1afc0826dca"
PRETRAINING_SHA256="f129fb2c953e7c87fae3f796c9c04c546943f0ad8518c0cfc795a85c1c4218e0"
CANARY_SHA256="5308b5a260d8a4dd467cfe833298f47b6c05ecb04047f0d114e052a36410cf67"
AUTH_ENV="GLM47_CHARM_R7_CANARY_AUTHORIZATION"
AUTH_PHRASE="I_AUTHORIZE_CHARM_R7_ADMITTED_MEF_EXACT40_CANARY_AND_GCP_COSTS"
RUN_ID="${1:-charm-r7-r87-canary-$(date -u +%Y%m%dT%H%M%SZ)}"
REMOTE_ROOT="${REMOTE_ROOT_BASE}/${RUN_ID}-stage-$(date -u +%Y%m%dT%H%M%SZ)-$$"
SOURCE_COMMIT="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
RUNTIME_ARCHIVE="$(mktemp --suffix=.tar.gz)"
RUNTIME_ARCHIVE_REL="runtime/${RUNTIME_DIRNAME}.tar.gz"
LOCAL_PREFLIGHT_RECEIPT="$(mktemp --suffix=.json)"

HASH_INPUTS=(
  scripts/gcp_full_v5_charm_grpo.py
  scripts/gcp_full_v5_charm_r7_canary_headless.sh
  scripts/train_grpo.sh
  scripts/check_runtime.py
  scripts/prepare_grpo_adapter.py
  scripts/convert_checkpoint.sh
  scripts/publish_results.py
  configs/full_v5_charm_grpo/gcp-r1.json
  "${CONFIG_REL}"
  "${CANARY_REL}"
  "${SELECTION_REL}"
  "${PRETRAINING_REL}"
  docker/full-v5-charm-grpo-gcp/Dockerfile
  docker/full-v5-charm-grpo-gcp/Verifier.Dockerfile
  examples/grpo.sh
  src/glm47_posttraining/__init__.py
  src/glm47_posttraining/constants.py
  src/glm47_posttraining/aider_polyglot
  src/glm47_posttraining/cpp_perf
  src/glm47_posttraining/integrations
)

if ! [[ "${RUN_ID}" =~ ^charm-r7-r87-canary-[A-Za-z0-9][A-Za-z0-9._-]{0,132}$ ]]; then
  echo "run ID must begin with charm-r7-r87-canary- and contain only safe characters" >&2
  exit 2
fi
if [[ "${!AUTH_ENV:-}" != "${AUTH_PHRASE}" ]]; then
  echo "${AUTH_ENV} must explicitly authorize this admitted 8xH100 canary and its GCP costs" >&2
  exit 2
fi
if ! [[ "${SOURCE_COMMIT}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "local source commit is not a lowercase 40-character Git SHA" >&2
  exit 2
fi
for path in "${HASH_INPUTS[@]}" "${RUNTIME_REL}"; do
  if [[ ! -e "${REPO_ROOT}/${path}" ]]; then
    echo "missing required R7 canary input: ${path}" >&2
    exit 2
  fi
done

STARTED_VM=0
cleanup_and_stop_after_failure() {
  exit_code=$?
  trap - EXIT
  rm -f -- "${RUNTIME_ARCHIVE}" "${LOCAL_PREFLIGHT_RECEIPT}"
  if [[ "${exit_code}" -ne 0 && "${STARTED_VM}" -eq 1 ]]; then
    echo "R7 canary startup failed after this command started the VM; stopping it to limit cost" >&2
    gcloud compute instances stop "${INSTANCE}" \
      --project="${PROJECT}" \
      --zone="${ZONE}" \
      --discard-local-ssd=false \
      --quiet || true
  fi
  exit "${exit_code}"
}
trap cleanup_and_stop_after_failure EXIT

# All deterministic, no-GPU gates happen before the VM is started.
printf '%s  %s\n' "${PRETRAINING_SHA256}" "${REPO_ROOT}/${PRETRAINING_REL}" | sha256sum --check --status
printf '%s  %s\n' "${CANARY_SHA256}" "${REPO_ROOT}/${CANARY_REL}" | sha256sum --check --status
(
  cd "${REPO_ROOT}"
  export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"
  export GLM47_FULL_V5_CONFIG_PATH="${REPO_ROOT}/${CONFIG_REL}"
  python3 scripts/gcp_full_v5_charm_grpo.py inspect >"${LOCAL_PREFLIGHT_RECEIPT}"
  python3 scripts/gcp_full_v5_charm_grpo.py render \
    --phase canary \
    --run-id "${RUN_ID}" >/dev/null
)
actual_runtime_tree="$(
  cd "${REPO_ROOT}"
  PYTHONPATH="${REPO_ROOT}/src" python3 -c 'import sys; from pathlib import Path; from glm47_posttraining.aider_polyglot.charm_grpo import tree_sha256; print(tree_sha256(Path(sys.argv[1])))' "${RUNTIME_REL}"
)"
if [[ "${actual_runtime_tree}" != "${RUNTIME_TREE_SHA256}" ]]; then
  echo "local R7 runtime tree mismatch: expected=${RUNTIME_TREE_SHA256} actual=${actual_runtime_tree}" >&2
  exit 2
fi

tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner \
  -czf "${RUNTIME_ARCHIVE}" \
  -C "${REPO_ROOT}/artifacts" \
  "${RUNTIME_DIRNAME}"
RUNTIME_ARCHIVE_SHA256="$(sha256sum "${RUNTIME_ARCHIVE}" | awk '{print $1}')"

provisioning_model="$(gcloud compute instances describe "${INSTANCE}" \
  --project="${PROJECT}" \
  --zone="${ZONE}" \
  --format='value(scheduling.provisioningModel)')"
if [[ "${provisioning_model}" != "SPOT" ]]; then
  echo "R7 canary requires SPOT scheduling; found ${provisioning_model}" >&2
  exit 2
fi

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
    STARTED_VM=1
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
    ~/${REMOTE_ROOT}/runtime \
    ~/${REMOTE_ROOT}/artifacts/charm-task-generation-v1/v1r87-20260812T122334Z/remediation-004 \
    ~/${REMOTE_ROOT}/configs/full_v5_charm_grpo \
    ~/${REMOTE_ROOT}/docker/full-v5-charm-grpo-gcp \
    ~/${REMOTE_ROOT}/examples \
    ~/${REMOTE_ROOT}/src/glm47_posttraining"

gcloud compute scp \
  "${REPO_ROOT}/scripts/gcp_full_v5_charm_grpo.py" \
  "${REPO_ROOT}/scripts/gcp_full_v5_charm_r7_canary_headless.sh" \
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
  "${REPO_ROOT}/${CONFIG_REL}" \
  "${REPO_ROOT}/${CANARY_REL}" \
  "${REPO_ROOT}/${SELECTION_REL}" \
  "${INSTANCE}:~/${REMOTE_ROOT}/configs/full_v5_charm_grpo/" \
  --project="${PROJECT}" \
  --zone="${ZONE}"
gcloud compute scp \
  "${REPO_ROOT}/${PRETRAINING_REL}" \
  "${INSTANCE}:~/${REMOTE_ROOT}/${PRETRAINING_REL}" \
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
gcloud compute scp \
  "${RUNTIME_ARCHIVE}" \
  "${INSTANCE}:~/${REMOTE_ROOT}/${RUNTIME_ARCHIVE_REL}" \
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
  --command="cd ~/${REMOTE_ROOT} && GLM47_SOURCE_COMMIT=${SOURCE_COMMIT} ${AUTH_ENV}=${AUTH_PHRASE} bash scripts/gcp_full_v5_charm_r7_canary_headless.sh ${RUN_ID} ${RUNTIME_ARCHIVE_REL} ${RUNTIME_ARCHIVE_SHA256}"

rm -f -- "${RUNTIME_ARCHIVE}" "${LOCAL_PREFLIGHT_RECEIPT}"
trap - EXIT
echo "R7_CANARY_RUN_ID=${RUN_ID}"
echo "R7_CANARY_REMOTE_ROOT=~/${REMOTE_ROOT}"
