#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

AWS_TF_DIR="${REPO_DIR}/infra/terraform/aws"

echo "[poststart] Starting port-forward manager"
bash "${SCRIPT_DIR}/port-forward-manager.sh"

if [ -d "${AWS_TF_DIR}" ]; then
  echo "[poststart] Terraform init/plan for AWS resources"
  (
    cd "${AWS_TF_DIR}"
    terraform init
    set +e
    terraform plan -detailed-exitcode -no-color >/tmp/terraform-aws-plan.log 2>&1
    plan_status=$?
    set -e
    if [ "${plan_status}" -eq 2 ]; then
      echo "[poststart] Terraform changes detected; applying"
      terraform apply -auto-approve
    elif [ "${plan_status}" -eq 0 ]; then
      echo "[poststart] No Terraform changes detected"
    else
      echo "[poststart] WARNING: terraform plan failed; see /tmp/terraform-aws-plan.log"
    fi
  )
else
  echo "[poststart] WARNING: ${AWS_TF_DIR} not found; skipping AWS terraform apply"
fi

if ! service cron status >/dev/null 2>&1; then
  echo "[poststart] Cron not running; restarting"
  sudo service cron restart
else
  echo "[poststart] Cron already running"
fi
