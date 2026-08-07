#!/usr/bin/env bash

# Start or resume the pinned public-PR evaluation VM when necessary, wait for
# it to become RUNNING, and then replace this process with an interactive SSH
# connection. Environment variables can override the recorded defaults.

PROJECT_ID="${PROJECT_ID:-lifeandhalf-24122025}"
VM_NAME="${VM_NAME:-glm47-synthmem-50ep-pr-eval}"
ZONE="${ZONE:-}"
MAX_POLLS="${MAX_POLLS:-90}"
POLL_SECONDS="${POLL_SECONDS:-10}"

usage() {
  cat <<'EOF'
Usage: scripts/start_gcp_public_pr_eval_vm.sh [gcloud compute ssh options]

Defaults:
  PROJECT_ID=lifeandhalf-24122025
  VM_NAME=glm47-synthmem-50ep-pr-eval
  ZONE=auto-detected

Optional environment overrides:
  PROJECT_ID, VM_NAME, ZONE, MAX_POLLS, POLL_SECONDS

Examples:
  scripts/start_gcp_public_pr_eval_vm.sh
  ZONE=us-central1-a scripts/start_gcp_public_pr_eval_vm.sh
  scripts/start_gcp_public_pr_eval_vm.sh --tunnel-through-iap
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
esac

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is not installed or is not on PATH" >&2
  exit 2
fi

if [[ ! "${MAX_POLLS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "MAX_POLLS must be a positive integer" >&2
  exit 2
fi

if [[ ! "${POLL_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
  echo "POLL_SECONDS must be a positive integer" >&2
  exit 2
fi

if [[ -z "${ZONE}" ]]; then
  ZONE_OUTPUT="$(
    gcloud compute instances list \
      --project="${PROJECT_ID}" \
      --filter="name=(${VM_NAME})" \
      --format='value(zone.basename())'
  )"
  LIST_RC="$?"

  if [[ "${LIST_RC}" -ne 0 ]]; then
    echo "Unable to list GCP instances in project ${PROJECT_ID}" >&2
    exit "${LIST_RC}"
  fi

  ZONE_COUNT="$(
    printf '%s\n' "${ZONE_OUTPUT}" |
      awk 'NF {count += 1} END {print count + 0}'
  )"

  if [[ "${ZONE_COUNT}" -eq 0 ]]; then
    echo "VM ${VM_NAME} was not found in project ${PROJECT_ID}" >&2
    exit 3
  fi

  if [[ "${ZONE_COUNT}" -ne 1 ]]; then
    echo "VM name ${VM_NAME} matched more than one zone; set ZONE explicitly" >&2
    exit 3
  fi

  ZONE="$(printf '%s\n' "${ZONE_OUTPUT}" | awk 'NF {print; exit}')"
fi

instance_status() {
  gcloud compute instances describe "${VM_NAME}" \
    --project="${PROJECT_ID}" \
    --zone="${ZONE}" \
    --format='value(status)'
}

STATUS="$(instance_status)"
STATUS_RC="$?"

if [[ "${STATUS_RC}" -ne 0 || -z "${STATUS}" ]]; then
  echo "Unable to read status for ${VM_NAME} in ${ZONE}" >&2
  exit 4
fi

START_REQUESTED=0
RESUME_REQUESTED=0

for ((POLL = 1; POLL <= MAX_POLLS; POLL += 1)); do
  case "${STATUS}" in
    RUNNING)
      break
      ;;
    TERMINATED)
      if [[ "${START_REQUESTED}" -eq 0 ]]; then
        echo "Starting ${VM_NAME} in ${ZONE}..."
        if ! gcloud compute instances start "${VM_NAME}" \
          --project="${PROJECT_ID}" \
          --zone="${ZONE}"; then
          echo "Failed to start ${VM_NAME}" >&2
          exit 5
        fi
        START_REQUESTED=1
      fi
      ;;
    SUSPENDED)
      if [[ "${RESUME_REQUESTED}" -eq 0 ]]; then
        echo "Resuming ${VM_NAME} in ${ZONE}..."
        if ! gcloud compute instances resume "${VM_NAME}" \
          --project="${PROJECT_ID}" \
          --zone="${ZONE}"; then
          echo "Failed to resume ${VM_NAME}" >&2
          exit 5
        fi
        RESUME_REQUESTED=1
      fi
      ;;
    PROVISIONING|STAGING|STOPPING|SUSPENDING|REPAIRING)
      echo "Waiting for ${VM_NAME}: status=${STATUS} poll=${POLL}/${MAX_POLLS}"
      ;;
    *)
      echo "Unsupported VM status: ${STATUS}" >&2
      exit 6
      ;;
  esac

  sleep "${POLL_SECONDS}"
  STATUS="$(instance_status)"
  STATUS_RC="$?"

  if [[ "${STATUS_RC}" -ne 0 || -z "${STATUS}" ]]; then
    echo "Unable to refresh VM status" >&2
    exit 4
  fi
done

if [[ "${STATUS}" != "RUNNING" ]]; then
  echo "VM did not reach RUNNING after ${MAX_POLLS} polls" >&2
  exit 7
fi

echo "Connecting to ${VM_NAME} (${PROJECT_ID}, ${ZONE})..."
echo "After login, use: tmux attach -t r5"

exec gcloud compute ssh "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  "$@"
