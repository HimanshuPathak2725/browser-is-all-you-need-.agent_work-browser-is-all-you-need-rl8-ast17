FROM radixark/miles:latest-cu12@sha256:efc8027fc47aaa9687dc4f1046093ed4e2f9789e52a932fcefb7031402aeff37

ENV PYTHONPATH=/opt/charm-grpo/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GLM47_LIBCLANG_RESOURCE_DIR=/usr/local/lib/clang/18 \
    TZ=UTC \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         ca-certificates docker.io git \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --no-deps libclang==18.1.1

WORKDIR /opt/charm-grpo
COPY src/glm47_posttraining/__init__.py src/glm47_posttraining/__init__.py
COPY src/glm47_posttraining/constants.py src/glm47_posttraining/constants.py
COPY src/glm47_posttraining/aider_polyglot src/glm47_posttraining/aider_polyglot
COPY src/glm47_posttraining/cpp_perf src/glm47_posttraining/cpp_perf
COPY src/glm47_posttraining/integrations src/glm47_posttraining/integrations
COPY scripts/train_grpo.sh scripts/train_grpo.sh
COPY scripts/check_runtime.py scripts/check_runtime.py
COPY scripts/prepare_grpo_adapter.py scripts/prepare_grpo_adapter.py
COPY scripts/reconstruct_megatron_lora.py scripts/reconstruct_megatron_lora.py
COPY scripts/convert_checkpoint.sh scripts/convert_checkpoint.sh
COPY scripts/publish_results.py scripts/publish_results.py
COPY scripts/run_charm_compiler_guided.py scripts/run_charm_compiler_guided.py
COPY examples/grpo.sh examples/grpo.sh
COPY artifacts/charm-compiler-grpo/r1/data data-source
COPY artifacts/charm-compiler-grpo/r1/executable-oracle-receipt.json evidence/executable-oracle-receipt.json
COPY configs/charm_compiler_grpo/r1.json configs/r1.json

RUN printf '%s  %s\n%s  %s\n%s  %s\n' \
      'de4bd2526327dc5a222df426b9fc986a3c6bf4c051b04e767450d412fa469fbb' \
      'data-source/manifest.json' \
      'a4ea9d320a127b4be36ad1aaeb4054df18b73a3a0250a4c2e209f23fc0b73ca8' \
      'data-source/grpo/train.jsonl' \
      'dbaa7af807ba1020822f75ccc8e6b0a5ba45e8afaf9971cd9a3c712d2c175ec4' \
      'evidence/executable-oracle-receipt.json' | sha256sum -c - \
    && python3 -m glm47_posttraining.integrations.miles_charm_compiler_grpo \
         validate-data --data-dir /opt/charm-grpo/data-source \
    && python3 -c 'from glm47_posttraining.aider_polyglot.ast_evaluator import validate_libclang_runtime; assert validate_libclang_runtime()' \
    && test ! -e scripts/build_public_pr_eval_v2.py \
    && test ! -e src/glm47_posttraining/public_pr_eval \
    && ! grep -R -F 'fmtlib-fmt-large-time-point-overflow-v2' \
         src scripts examples data-source

CMD ["/bin/bash"]
