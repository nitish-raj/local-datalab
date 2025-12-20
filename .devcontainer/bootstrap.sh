#!/usr/bin/env bash
set -euo pipefail

CLUSTER_PROFILE="local-datalab"
TF_DIR="/workspaces/$(basename "$(pwd)")/infra/terraform"

echo "[bootstrap] Starting minikube"
minikube start --profile "${CLUSTER_PROFILE}" --driver=docker --cpus=4 --memory=8192 --disk-size=40g
minikube -p "${CLUSTER_PROFILE}" addons enable metrics-server

echo "[bootstrap] Setting kubectl context"
kubectl config use-context "${CLUSTER_PROFILE}"

echo "[bootstrap] Kubernetes nodes"
kubectl get nodes

# echo "[bootstrap] Deploy Kubernetes resources first"
# cd "${TF_DIR}"
# terraform init
# terraform apply -auto-approve

# echo "[bootstrap] Setup localstack port-forward for Terraform"
# kubectl port-forward svc/localstack 4566:4566 -n data-lab >/tmp/localstack-port-forward.log 2>&1 &

# kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow >/tmp/airflow-port-forward.log 2>&1 &
# echo "[bootstrap] Airflow webserver available at http://localhost:8080"

echo "[bootstrap] Wiring VS Code Kubernetes extension tools (kubectl, helm, minikube)"

TOOLS_ROOT="/home/vscode/.local/state/vs-kubernetes/tools"

# helm and minikube: ../tools/linux-amd64/<tool>
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

#  kubectl: ../tools/kubectl/kubectl
if command -v kubectl >/dev/null 2>&1; then
  KUBECTL_BIN="$(command -v kubectl)"
  KUBECTL_DIR="${TOOLS_ROOT}/kubectl"
  mkdir -p "${KUBECTL_DIR}"
  ln -sf "${KUBECTL_BIN}" "${KUBECTL_DIR}/kubectl"
  echo "[bootstrap] Linked kubectl (${KUBECTL_BIN}) -> ${KUBECTL_DIR}/kubectl"
else
  echo "[bootstrap] WARNING: kubectl not found on PATH; skipping wiring"
fi

echo "[bootstrap] Setup complete"
