FROM radixark/miles:latest-cu12@sha256:efc8027fc47aaa9687dc4f1046093ed4e2f9789e52a932fcefb7031402aeff37

ARG AIDER_COMMIT=5dc9490bb35f9729ef2c95d00a19ccd30c26339c
ENV PYTHONPATH=/opt/public-pr-eval/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CC=gcc-13 \
    CXX=g++-13 \
    TZ=UTC \
    LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
      software-properties-common git make curl python3-venv ca-certificates \
    && add-apt-repository -y ppa:ubuntu-toolchain-r/test \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc-13 g++-13 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100 \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --no-deps --force-reinstall \
      sglang-kernel==0.4.4 --index-url https://docs.sglang.ai/whl/cu129/ \
    && python3 -m pip install --no-cache-dir cmake==3.27.9 \
    && cmake --version | head -1 | grep -Fx "cmake version 3.27.9"

RUN git clone https://github.com/Aider-AI/aider.git /aider \
    && git -C /aider checkout --detach "${AIDER_COMMIT}" \
    && python3 -m venv /opt/aider-venv \
    && /opt/aider-venv/bin/python -m pip install --no-cache-dir -e '/aider[dev]'

WORKDIR /opt/public-pr-eval
COPY configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl
COPY configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl
COPY configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl
COPY configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl
COPY configs/public_pr_eval/private_probes configs/public_pr_eval/private_probes
COPY src/glm47_posttraining/public_pr_eval src/glm47_posttraining/public_pr_eval
COPY scripts/public_pr_repo_eval.py scripts/public_pr_repo_eval.py
COPY scripts/validate_public_pr_eval.py scripts/validate_public_pr_eval.py
COPY scripts/gcp_public_pr_synthmem_50ep_eval.py scripts/gcp_public_pr_synthmem_50ep_eval.py

RUN printf '%s  %s\n%s  %s\n' \
      '316e293ecf3a183b1f14612007e47edfbbea3e2b72ee5349b95b12d0a779ec82' \
      'configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl' \
      '9db4bbc4df06aed1cb87dca1026456f2cafa3973f15024fba41b3c912d5b22a7' \
      'configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl' | sha256sum -c -
RUN printf '%s  %s\n' \
      '01d2015df04766726b778948997be9d34aa48cba1e78c002d92429b582e0765c' \
      'configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl' | sha256sum -c -
RUN printf '%s  %s\n' \
      '03ed4454a8953b80b09325392c0045e9ea0ba64b6c483ea886c3850ffbd7c7a3' \
      'configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl' | sha256sum -c -

RUN python3 scripts/validate_public_pr_eval.py \
      configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl \
      --out /tmp/public-pr-static-validation-full.json \
    && python3 scripts/public_pr_repo_eval.py prepare \
      configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl \
      --output /opt/public-pr-prepared/full \
    && cp /tmp/public-pr-static-validation-full.json /opt/public-pr-prepared/full/static-validation.json \
    && python3 scripts/public_pr_repo_eval.py verify-oracles \
      configs/public_pr_eval/public-pr-repo-eval-v2-r5.jsonl \
      --prepared-root /opt/public-pr-prepared/full \
      --output /opt/public-pr-oracles/full

RUN python3 scripts/validate_public_pr_eval.py \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl \
      --out /tmp/public-pr-static-validation-demo-fmtlib.json \
    && python3 scripts/public_pr_repo_eval.py prepare \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl \
      --output /opt/public-pr-prepared/demo-fmtlib \
    && cp /tmp/public-pr-static-validation-demo-fmtlib.json /opt/public-pr-prepared/demo-fmtlib/static-validation.json \
    && python3 scripts/public_pr_repo_eval.py verify-oracles \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v2.jsonl \
      --prepared-root /opt/public-pr-prepared/demo-fmtlib \
      --output /opt/public-pr-oracles/demo-fmtlib

RUN python3 scripts/validate_public_pr_eval.py \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl \
      --out /tmp/public-pr-static-validation-demo-fmtlib-v3.json \
    && python3 scripts/public_pr_repo_eval.py prepare \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl \
      --output /opt/public-pr-prepared/demo-fmtlib-v3 \
    && cp /tmp/public-pr-static-validation-demo-fmtlib-v3.json /opt/public-pr-prepared/demo-fmtlib-v3/static-validation.json \
    && python3 scripts/public_pr_repo_eval.py verify-oracles \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v3.jsonl \
      --prepared-root /opt/public-pr-prepared/demo-fmtlib-v3 \
      --output /opt/public-pr-oracles/demo-fmtlib-v3

RUN python3 scripts/validate_public_pr_eval.py \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl \
      --out /tmp/public-pr-static-validation-demo-fmtlib-v4.json \
    && python3 scripts/public_pr_repo_eval.py prepare \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl \
      --output /opt/public-pr-prepared/demo-fmtlib-v4 \
    && cp /tmp/public-pr-static-validation-demo-fmtlib-v4.json /opt/public-pr-prepared/demo-fmtlib-v4/static-validation.json \
    && python3 scripts/public_pr_repo_eval.py verify-oracles \
      configs/public_pr_eval/public-pr-repo-eval-demo-fmtlib-v4.jsonl \
      --prepared-root /opt/public-pr-prepared/demo-fmtlib-v4 \
      --output /opt/public-pr-oracles/demo-fmtlib-v4

RUN /opt/aider-venv/bin/python -m pip freeze | LC_ALL=C sort > /opt/public-pr-prepared/aider-pip-freeze.txt

ENTRYPOINT ["python3", "/opt/public-pr-eval/scripts/gcp_public_pr_synthmem_50ep_eval.py"]
