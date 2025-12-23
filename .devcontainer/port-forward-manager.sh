#!/usr/bin/env bash
set -euo pipefail

LOG_DIR="/tmp"
AIRFLOW_LOG="${LOG_DIR}/airflow-port-forward.log"
LOCALSTACK_LOG="${LOG_DIR}/localstack-port-forward.log"
PID_DIR="/tmp/port-forward-pids"

mkdir -p "${PID_DIR}"

kill_existing_forwards() {
    if [ -f "${PID_DIR}/airflow.pid" ]; then
        kill $(cat "${PID_DIR}/airflow.pid") 2>/dev/null || true
        rm "${PID_DIR}/airflow.pid"
    fi
    if [ -f "${PID_DIR}/localstack.pid" ]; then
        kill $(cat "${PID_DIR}/localstack.pid") 2>/dev/null || true
        rm "${PID_DIR}/localstack.pid"
    fi
    pkill -f "kubectl port-forward.*airflow-api-server" 2>/dev/null || true
    pkill -f "kubectl port-forward.*localstack" 2>/dev/null || true
}

start_airflow_forward() {
    echo "[$(date)] Starting Airflow port-forward..." >> "${AIRFLOW_LOG}"
    nohup kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >> "${AIRFLOW_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/airflow.pid"
    disown %1 2>/dev/null || true
}

start_localstack_forward() {
    echo "[$(date)] Starting LocalStack port-forward..." >> "${LOCALSTACK_LOG}"
    nohup kubectl port-forward svc/localstack 4566:4566 -n data-lab >> "${LOCALSTACK_LOG}" 2>&1 &
    echo $! > "${PID_DIR}/localstack.pid"
    disown %1 2>/dev/null || true
}

wait_for_service_ready() {
    local svc_name="$1"
    local ns="$2"
    local max_wait=60
    local count=0

    while [ $count -lt $max_wait ]; do
        if kubectl get svc "$svc_name" -n "$ns" >/dev/null 2>&1; then
            return 0
        fi
        sleep 2
        count=$((count + 2))
    done
    echo "[$(date)] ERROR: Service $svc_name not ready after ${max_wait}s" >> "${AIRFLOW_LOG}"
    return 1
}

echo "[$(date)] Port-forward manager starting..."
kill_existing_forwards

wait_for_service_ready "airflow-api-server" "airflow"
start_airflow_forward

wait_for_service_ready "localstack" "data-lab"
start_localstack_forward

echo "[$(date)] Port-forwards started. Watching for crashes..."

while true; do
    sleep 5

    if [ -f "${PID_DIR}/airflow.pid" ]; then
        if ! kill -0 $(cat "${PID_DIR}/airflow.pid") 2>/dev/null; then
            echo "[$(date)] Airflow port-forward died, restarting..." >> "${AIRFLOW_LOG}"
            start_airflow_forward
        fi
    else
        echo "[$(date)] Airflow PID file missing, starting..." >> "${AIRFLOW_LOG}"
        start_airflow_forward
    fi

    if [ -f "${PID_DIR}/localstack.pid" ]; then
        if ! kill -0 $(cat "${PID_DIR}/localstack.pid") 2>/dev/null; then
            echo "[$(date)] LocalStack port-forward died, restarting..." >> "${LOCALSTACK_LOG}"
            start_localstack_forward
        fi
    else
        echo "[$(date)] LocalStack PID file missing, starting..." >> "${LOCALSTACK_LOG}"
        start_localstack_forward
    fi
done
