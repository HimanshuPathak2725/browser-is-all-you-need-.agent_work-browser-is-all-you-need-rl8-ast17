FROM gcc:13

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
         ca-certificates coreutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
