FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

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

COPY .devcontainer/requirements.txt /tmp/requirements.txt
RUN uv pip install --system --upgrade pip
RUN uv pip install --system --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt