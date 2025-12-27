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

# Avoid locale warning about /etc/environment by using /etc/default/locale
RUN sed -i '/^LANG=/d' /etc/environment && \
    printf 'LANG="C.UTF-8"\n' > /etc/default/locale

COPY .devcontainer/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt