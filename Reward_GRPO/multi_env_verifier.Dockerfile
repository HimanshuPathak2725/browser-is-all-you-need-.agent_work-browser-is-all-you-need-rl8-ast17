FROM gcc:13.3.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LC_ALL=C \
    LANG=C

RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake make util-linux python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
