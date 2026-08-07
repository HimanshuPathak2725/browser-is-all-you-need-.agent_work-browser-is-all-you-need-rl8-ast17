#!/usr/bin/env bash
set -euo pipefail

TOOLKIT_VERSION="1.19.1-1"

if [[ "$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)" -ne 4 ]]; then
  echo "Expected exactly four GPUs" >&2
  exit 2
fi
if nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | \
    awk -F, '$1 !~ /A100/ || $2 + 0 < 80000 { bad=1 } END { exit bad }'; then
  echo "Verified four A100 80GB GPUs"
else
  echo "GPU type or memory does not match four full A100 80GB devices" >&2
  exit 2
fi

sudo apt-get update
sudo apt-get install -y --no-install-recommends docker.io ca-certificates curl gnupg2
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -sSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
sudo apt-get update
sudo apt-get install -y \
  "nvidia-container-toolkit=${TOOLKIT_VERSION}" \
  "nvidia-container-toolkit-base=${TOOLKIT_VERSION}" \
  "libnvidia-container-tools=${TOOLKIT_VERSION}" \
  "libnvidia-container1=${TOOLKIT_VERSION}"
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl enable --now docker
sudo systemctl restart docker
sudo docker info >/dev/null
echo "Docker and NVIDIA Container Toolkit ${TOOLKIT_VERSION} are ready"
