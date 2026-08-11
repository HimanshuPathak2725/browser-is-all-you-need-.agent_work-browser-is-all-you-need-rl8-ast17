FROM gcc:13

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         ca-certificates cmake coreutils make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

LABEL org.opencontainers.image.title="GLM-4.7 full-v5 CHARM verifier" \
      glm47.network="none" \
      glm47.modal.policy="denied"
