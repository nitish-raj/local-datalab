FROM mcr.microsoft.com/devcontainers/python:3.13-bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iputils-ping \
        dnsutils \
        cron \
        curl unzip groff less \
        gnupg software-properties-common ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements/dev.txt /tmp/requirements-dev.txt
RUN uv pip install --system --no-cache-dir -r /tmp/requirements-dev.txt && \
    rm -f /tmp/requirements-dev.txt
