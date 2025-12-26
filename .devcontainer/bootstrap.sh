#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${KUBE_CONTEXT:?KUBE_CONTEXT env var must be set}"
K8_TF_DIR="${REPO_DIR}/infra/terraform/k8"
AWS_TF_DIR="${REPO_DIR}/infra/terraform/aws"

echo "[bootstrap] Wiring VS Code Kubernetes extension tools (kubectl, helm, minikube)"
TOOLS_ROOT="/home/vscode/.local/state/vs-kubernetes/tools"

# symlink helm and minikube: ../tools/linux-amd64/<tool>
for tool in helm minikube; do
  if command -v "${tool}" >/dev/null 2>&1; then
    BIN_PATH="$(command -v "${tool}")"
    TOOL_DIR="${TOOLS_ROOT}/${tool}/linux-amd64"
    mkdir -p "${TOOL_DIR}"
    ln -sf "${BIN_PATH}" "${TOOL_DIR}/${tool}"
    echo "[bootstrap] Linked ${tool} (${BIN_PATH}) -> ${TOOL_DIR}/${tool}"
  else
    echo "[bootstrap] WARNING: ${tool} not found on PATH; skipping wiring"
  fi
done

#  symlink kubectl: ../tools/kubectl/kubectl
if command -v kubectl >/dev/null 2>&1; then
  KUBECTL_BIN="$(command -v kubectl)"
  KUBECTL_DIR="${TOOLS_ROOT}/kubectl"
  mkdir -p "${KUBECTL_DIR}"
  ln -sf "${KUBECTL_BIN}" "${KUBECTL_DIR}/kubectl"
  echo "[bootstrap] Linked kubectl (${KUBECTL_BIN}) -> ${KUBECTL_DIR}/kubectl"
else
  echo "[bootstrap] WARNING: kubectl not found on PATH; skipping wiring"
fi

if [[ -n "${TF_PLUGIN_CACHE_DIR:-}" ]]; then
  mkdir -p "${TF_PLUGIN_CACHE_DIR}"
fi

terraform_init_with_retry() {
    local dir="$1"
    local max_attempts="${2:-3}"
    local attempt=1
    local delay=5

    while (( attempt <= max_attempts )); do
        echo "[bootstrap] terraform init (attempt ${attempt}/${max_attempts}) in ${dir}"
        if (cd "${dir}" && terraform init); then
            return 0
        fi

        if (( attempt == max_attempts )); then
            return 1
        fi

        echo "[bootstrap] terraform init failed; retrying in ${delay}s"
        sleep "${delay}"
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done
}

detect_system_resources() {
    local os_type
    os_type="$(uname -s)"
    
    # Detect available CPUs
    if [[ "$os_type" == "Darwin" ]]; then
        AVAILABLE_CPUS="$(sysctl -n hw.ncpu)"
    elif [[ "$os_type" == "Linux" ]]; then
        AVAILABLE_CPUS="$(nproc)"
    else
        AVAILABLE_CPUS=2
    fi
    
    # Detect available memory in MB
    if [[ "$os_type" == "Darwin" ]]; then
        TOTAL_MEM_BYTES="$(sysctl -n hw.memsize)"
        AVAILABLE_MEM_MB="$((TOTAL_MEM_BYTES / 1024 / 1024))"
    elif [[ "$os_type" == "Linux" ]]; then
        TOTAL_MEM_KB="$(grep MemTotal /proc/meminfo | awk '{print $2}')"
        AVAILABLE_MEM_MB="$((TOTAL_MEM_KB / 1024))"
    else
        AVAILABLE_MEM_MB=4096
    fi
    
    # Detect available disk space in GB (check minikube default location)
    if [[ "$os_type" == "Darwin" ]]; then
        MINIKUBE_HOME="${HOME}/.minikube"
        AVAILABLE_DISK_GB="$(df -h "$MINIKUBE_HOME" 2>/dev/null | awk 'NR==2 {gsub(/[^0-9.]/,"",$4); print $4}' || echo "30")"
    elif [[ "$os_type" == "Linux" ]]; then
        MINIKUBE_HOME="${HOME}/.minikube"
        AVAILABLE_DISK_GB="$(df -h "$MINIKUBE_HOME" 2>/dev/null | awk 'NR==2 {gsub(/[^0-9.]/,"",$4); print $4}' || echo "30")"
    else
        AVAILABLE_DISK_GB=30
    fi
    
    # Calculate minikube resources (use 100% of available)
    MINIKUBE_CPUS=$AVAILABLE_CPUS
    [[ $MINIKUBE_CPUS -lt 2 ]] && MINIKUBE_CPUS=2
    
    MINIKUBE_MEMORY=$AVAILABLE_MEM_MB
    [[ $MINIKUBE_MEMORY -lt 2048 ]] && MINIKUBE_MEMORY=2048
    
    MINIKUBE_DISK="${AVAILABLE_DISK_GB%.0}"
    [[ $MINIKUBE_DISK -lt 10 ]] && MINIKUBE_DISK=10
    
    echo "[bootstrap] System resources detected:"
    echo "  CPUs: ${AVAILABLE_CPUS} (allocating ${MINIKUBE_CPUS})"
    echo "  Memory: ${AVAILABLE_MEM_MB}MB (allocating ${MINIKUBE_MEMORY}MB)"
    echo "  Disk: ${AVAILABLE_DISK_GB}GB available (allocating ${MINIKUBE_DISK}GB)"
}

detect_system_resources

echo "[bootstrap] Starting minikube"
minikube start --profile "${KUBE_CONTEXT}" --cpus="${MINIKUBE_CPUS}" --memory="${MINIKUBE_MEMORY}" --disk-size="${MINIKUBE_DISK}g"
minikube -p "${KUBE_CONTEXT}" addons enable metrics-server

echo "[bootstrap] Setting kubectl context"
kubectl config use-context "${KUBE_CONTEXT}"

echo "[bootstrap] Kubernetes nodes"
kubectl get nodes

echo "[bootstrap] Building Airflow image in minikube docker"
if command -v docker >/dev/null 2>&1; then
  eval "$(minikube -p "${KUBE_CONTEXT}" docker-env)"
  docker build -t local/airflow:dev -f "${REPO_DIR}/airflow/Dockerfile" "${REPO_DIR}"
else
  echo "[bootstrap] WARNING: docker not found on PATH; skipping Airflow image build"
fi

echo "[bootstrap] Deploy Kubernetes resources first"
terraform_init_with_retry "${K8_TF_DIR}"
cd "${K8_TF_DIR}"
terraform apply -auto-approve

echo "[bootstrap] Setup localstack port-forward for Terraform"
nohup kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &
disown %1 2>/dev/null || true
sleep 10

echo "[bootstrap] Deploy AWS resources"
terraform_init_with_retry "${AWS_TF_DIR}"
cd "${AWS_TF_DIR}"
terraform apply -auto-approve

sleep 10
nohup kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
disown %1 2>/dev/null || true
echo "[bootstrap] Airflow webserver available at http://localhost:8080"

echo "[bootstrap] Ensuring cron DAG sync job is installed"
SYNC_SCRIPT="${REPO_DIR}/.devcontainer/sync-dags.sh"
CRON_LINE="*/1 * * * * /bin/bash ${SYNC_SCRIPT} >> /tmp/sync-dags.log 2>&1"

if [ -f "${SYNC_SCRIPT}" ]; then
  if command -v crontab >/dev/null 2>&1; then
    ( crontab -l 2>/dev/null | grep -v 'sync-dags.sh' || true; echo "${CRON_LINE}" ) | crontab -
    echo "[bootstrap] Installed/updated cron entry for sync-dags.sh"
  else
    echo "[bootstrap] WARNING: crontab binary not found; skipping cron job install"
  fi
else
  echo "[bootstrap] WARNING: ${SYNC_SCRIPT} not found; cron job not installed"
fi

sudo service cron restart

echo "[bootstrap] Setup complete"
