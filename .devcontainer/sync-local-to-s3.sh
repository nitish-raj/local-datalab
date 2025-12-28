#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

# Load .env for cron (minimal environment)
ENV_FILE="${REPO_DIR}/.env"
if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

AWS_BIN="/usr/local/bin/aws"
AWS_ENDPOINT_URL="${AWS_ENDPOINT_URL:-${AIRFLOW__AWS__ENDPOINT_URL:-http://127.0.0.1:4566}}"

export AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-test}"
export AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-test}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-central-1}"

AIRFLOW_DAGS_BUCKET="${AIRFLOW_DAGS_BUCKET:-airflow-dags}"
RAW_SATELLITE_BUCKET="${RAW_SATELLITE_BUCKET:-raw-satellite-data}"

if ! command -v "${AWS_BIN}" >/dev/null 2>&1; then
  echo "[sync-local-to-s3] ERROR: aws CLI not found on PATH" >&2
  exit 1
fi

"${AWS_BIN}" --endpoint-url="${AWS_ENDPOINT_URL}" s3 sync \
  ./airflow/dags "s3://${AIRFLOW_DAGS_BUCKET}/dags" \
  --exclude "*" --include "*.py" --delete

"${AWS_BIN}" --endpoint-url="${AWS_ENDPOINT_URL}" s3 sync \
  ./airflow/data "s3://${RAW_SATELLITE_BUCKET}" --delete
