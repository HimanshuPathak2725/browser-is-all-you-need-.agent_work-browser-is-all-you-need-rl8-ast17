#!/usr/bin/env bash
set -euo pipefail

# The generated program sees only its current task, a read-only toolchain,
# a temporary directory, and a seccomp policy that denies socket creation.
# In particular it cannot inherit OPENAI_API_KEY, MODAL_*, W&B, AWS, or
# Hugging Face secrets. Explicit non-network namespace flags avoid Modal
# gVisor's nested network-namespace loopback limitation.
task_dir="$(pwd -P)"
task_name="$(basename "${task_dir}")"
sandbox_task_dir="/task/${task_name}"

exec env -i \
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  TMPDIR=/tmp \
  bwrap \
    --unshare-user-try \
    --unshare-ipc \
    --unshare-pid \
    --unshare-uts \
    --unshare-cgroup-try \
    --die-with-parent \
    --new-session \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin \
    --symlink usr/lib /lib \
    --symlink usr/lib64 /lib64 \
    --ro-bind /etc /etc \
    --proc /proc \
    --dev /dev \
    --tmpfs /tmp \
    --dir /task \
    --bind "${task_dir}" "${sandbox_task_dir}" \
    --chdir "${sandbox_task_dir}" \
    /usr/local/bin/cleanroom-no-network-exec \
    /bin/bash -euo pipefail -c '
      private_log=.cleanroom-private-test-output.log
      set +e
      (
        set -e
        mkdir -p build
        cd build
        cmake -DEXERCISM_RUN_ALL_TESTS=1 -G "Unix Makefiles" ..
        make
      ) >>"${private_log}" 2>&1
      status=$?
      set -e
      if [[ ${status} -eq 0 ]]; then
        echo "Private tests passed."
      else
        echo "Private tests failed. No private test names or output are disclosed."
      fi
      exit "${status}"
    '
