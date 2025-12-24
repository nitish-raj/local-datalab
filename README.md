[![terraform-validate](https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml/badge.svg)](https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml)
[![python-test](https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml/badge.svg)](https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml)

# Local Data Lab

Local Data Lab is a containerized, local-first data platform based on Airflow and Localstack on Minikube (k8) and deployed using Terraform for pipelines and infrastructure.

## System Requirements
- macOS, Linux, or Windows (with WSL2) capable of running Docker
- 4 CPU cores minimum (8 recommended for smoother Minikube + Localstack)
- 8 GB RAM minimum (16 GB recommended)
- 10+ GB free disk space for images, caches, and Terraform providers
- Hardware virtualization enabled (required by Docker Desktop/WSL2)

## Devcontainer Prerequisites
- Docker Desktop or Docker Engine with Compose v2
  - Install: https://docs.docker.com/get-docker/
  - Must allow privileged containers and bind-mounting the repo directory
- VS Code with the Dev Containers extension (or a compatible devcontainer CLI)
- Git
- Network access to pull images and features from Docker Hub/GHCR and Terraform providers
- A local `.env` file at repo root
  - Use the existing `.env` as a template and replace values for your environment as needed

## Run In Devcontainer
1. Open this repo in VS Code.
2. Run "Dev Containers: Reopen in Container".
3. The container build will run `.devcontainer/bootstrap.sh` on first start; it provisions Minikube, applies Terraform, and starts port forwards. This may take 10-20 minutes depending on system resources and network speed.
4. After the container starts, access services:
   - Airflow UI: http://localhost:8080 (default user: `admin`, password: `admin`)
   - Localstack UI: http://localhost:4566
   - Minikube Dashboard: Run `minikube dashboard -p local-datalab --url` in the devcontainer terminal to get the URL.
