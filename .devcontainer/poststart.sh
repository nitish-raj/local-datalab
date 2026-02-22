#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AWS_TF_DIR="${REPO_DIR}/infra/terraform/aws"

LOG_DIR="/tmp"
AIRFLOW_LOG="${LOG_DIR}/airflow-port-forward.log"
LOCALSTACK_LOG="${LOG_DIR}/localstack-port-forward.log"
ANALYTICS_DB_LOG="${LOG_DIR}/analytics-db-port-forward.log"
PID_DIR="/tmp/port-forward-pids"

: "${KUBE_CONTEXT:?KUBE_CONTEXT env var must be set}"
AIRFLOW_NAMESPACE="${AIRFLOW_NAMESPACE:-airflow}"
AIRFLOW_SERVICE_NAME="airflow-api-server"
LOCALSTACK_NAMESPACE="${DATA_LAB_NAMESPACE:-data-lab}"
ANALYTICS_DB_SERVICE_NAME="analytics-postgres"

mkdir -p "${PID_DIR}"

ensure_minikube_running() {
    if ! command -v minikube >/dev/null 2>&1; then
        echo "[$(date)] WARNING: minikube not found on PATH; skipping minikube start" >> "${AIRFLOW_LOG}"
        return 0
    fi

    if minikube status -p "${KUBE_CONTEXT}" >/dev/null 2>&1; then
        return 0
    fi

    echo "[$(date)] Starting minikube profile ${KUBE_CONTEXT}..." >> "${AIRFLOW_LOG}"
    minikube start -p "${KUBE_CONTEXT}" >> "${AIRFLOW_LOG}" 2>&1
}

set_kube_context() {
    if command -v kubectl >/dev/null 2>&1; then
        kubectl config use-context "${KUBE_CONTEXT}" >/dev/null 2>&1 || true
    fi
}

kill_existing_forwards() {
    if [ -f "${PID_DIR}/airflow.pid" ]; then
        kill $(cat "${PID_DIR}/airflow.pid") 2>/dev/null || true
        rm "${PID_DIR}/airflow.pid"
    fi
    if [ -f "${PID_DIR}/localstack.pid" ]; then
        kill $(cat "${PID_DIR}/localstack.pid") 2>/dev/null || true
        rm "${PID_DIR}/localstack.pid"
    fi
    if [ -f "${PID_DIR}/analytics-db.pid" ]; then
        kill $(cat "${PID_DIR}/analytics-db.pid") 2>/dev/null || true
        rm "${PID_DIR}/analytics-db.pid"
    fi
    pkill -f "kubectl port-forward.*airflow-api-server" 2>/dev/null || true
    pkill -f "kubectl port-forward.*localstack" 2>/dev/null || true
    pkill -f "kubectl port-forward.*analytics-postgres" 2>/dev/null || true
}

start_airflow_forward() {
    echo "[$(date)] Starting Airflow port-forward (${AIRFLOW_SERVICE_NAME})..." >> "${AIRFLOW_LOG}"
    nohup kubectl port-forward "svc/${AIRFLOW_SERVICE_NAME}" 8080:8080 -n "${AIRFLOW_NAMESPACE}" >> "${AIRFLOW_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/airflow.pid"
    disown %1 2>/dev/null || true
}

start_localstack_forward() {
    echo "[$(date)] Starting LocalStack port-forward..." >> "${LOCALSTACK_LOG}"
    nohup kubectl port-forward svc/localstack 4566:4566 -n "${LOCALSTACK_NAMESPACE}" >> "${LOCALSTACK_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/localstack.pid"
    disown %1 2>/dev/null || true
}

start_analytics_db_forward() {
    echo "[$(date)] Starting analytics Postgres port-forward..." >> "${ANALYTICS_DB_LOG}"
    nohup kubectl port-forward "svc/${ANALYTICS_DB_SERVICE_NAME}" 5432:5432 -n "${LOCALSTACK_NAMESPACE}" >> "${ANALYTICS_DB_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/analytics-db.pid"
    disown %1 2>/dev/null || true
}

wait_for_services_settle() {
    local delay_seconds=120
    echo "[$(date)] Waiting ${delay_seconds}s for services to be available..."
    local remaining
    for ((remaining=delay_seconds; remaining>0; remaining-=10)); do
        printf "[poststart] Services wait: %3ds remaining...\n" "${remaining}"
        sleep 10
    done
}

run_port_forward_manager() {
  echo "[$(date)] Port-forward manager starting..."
  ensure_minikube_running
  set_kube_context
  kill_existing_forwards
  wait_for_services_settle

  start_airflow_forward
  start_localstack_forward
  start_analytics_db_forward

  echo "[$(date)] Port-forwards started."
}

echo "[poststart] Starting port-forward manager"
run_port_forward_manager

if ! service cron status >/dev/null 2>&1; then
  echo "[poststart] Cron not running; restarting"
  sudo service cron restart
else
  echo "[poststart] Cron already running"
fi

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
