#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

export UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/rl8-ast17-uv-cache}"

exec uv run --extra cleanroom-eval python \
  scripts/run_luna_pass2_8x.py "$@"
