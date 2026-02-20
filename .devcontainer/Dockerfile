FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iputils-ping \
        dnsutils \
        cron \
        curl unzip groff less \
        gnupg software-properties-common ca-certificates && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g opencode-ai && \
    DEV_HOME="$(getent passwd 1000 | cut -d: -f6 || true)" && \
    if [ -n "${DEV_HOME}" ]; then \
      mkdir -p "${DEV_HOME}/.config/opencode" "${DEV_HOME}/.local/share/opencode" "${DEV_HOME}/.local/state" && \
      chown -R 1000:1000 "${DEV_HOME}/.config" "${DEV_HOME}/.local"; \
    fi && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements/dev.txt /tmp/requirements-dev.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements-dev.txt && \
    rm -f /tmp/requirements-dev.txt
