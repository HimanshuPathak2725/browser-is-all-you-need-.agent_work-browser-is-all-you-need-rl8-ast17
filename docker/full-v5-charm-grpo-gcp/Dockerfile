FROM radixark/miles:latest-cu12@sha256:efc8027fc47aaa9687dc4f1046093ed4e2f9789e52a932fcefb7031402aeff37

ENV PYTHONPATH=/opt/full-v5-charm/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CPLUS_INCLUDE_PATH=/usr/local/lib/clang/18/include \
    TZ=UTC \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         ca-certificates docker.io git rsync \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --no-deps libclang==18.1.1

WORKDIR /opt/full-v5-charm
COPY src/glm47_posttraining/__init__.py src/glm47_posttraining/__init__.py
COPY src/glm47_posttraining/constants.py src/glm47_posttraining/constants.py
COPY src/glm47_posttraining/aider_polyglot src/glm47_posttraining/aider_polyglot
COPY src/glm47_posttraining/cpp_perf src/glm47_posttraining/cpp_perf
COPY src/glm47_posttraining/integrations src/glm47_posttraining/integrations
COPY scripts/train_grpo.sh scripts/train_grpo.sh
COPY scripts/check_runtime.py scripts/check_runtime.py
COPY scripts/prepare_grpo_adapter.py scripts/prepare_grpo_adapter.py
COPY scripts/convert_checkpoint.sh scripts/convert_checkpoint.sh
COPY scripts/publish_results.py scripts/publish_results.py
COPY examples/grpo.sh examples/grpo.sh
COPY configs/full_v5_charm_grpo/gcp-r1.json configs/gcp-r1.json

RUN python3 -c 'from glm47_posttraining.aider_polyglot.ast_evaluator import validate_libclang_runtime; assert validate_libclang_runtime()' \
    && python3 -c 'from glm47_posttraining.aider_polyglot.full_v5_charm import SCHEDULE_KIND; assert SCHEDULE_KIND == "aider-cpp-rl-full-v5-charm-schedule"' \
    && test ! -e examples/modal \
    && test ! -e src/glm47_posttraining/public_pr_eval

LABEL org.opencontainers.image.title="GLM-4.7 full-v5 CHARM GRPO on GCP" \
      org.opencontainers.image.description="Modal-free, admission-gated 8xH100 GRPO runtime" \
      glm47.execution.cloud="gcp" \
      glm47.modal.policy="denied"

CMD ["/bin/bash"]
