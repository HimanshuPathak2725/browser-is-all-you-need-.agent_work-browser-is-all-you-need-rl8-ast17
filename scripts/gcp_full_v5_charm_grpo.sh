#!/usr/bin/env bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)" || exit 2
exec python3 "${SCRIPT_DIR}/gcp_full_v5_charm_grpo.py" "$@"
