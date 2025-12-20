#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_DIR}"

AWS_BIN="/usr/local/bin/aws"

AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
AWS_DEFAULT_REGION=eu-central-1 \
"${AWS_BIN}" --endpoint-url=http://127.0.0.1:4566 s3 sync \
  ./airflow s3://airflow-dags/dags --delete
