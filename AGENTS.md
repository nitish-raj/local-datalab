# Repository Guidelines

## Project Structure & Module Organization
- `airflow/dags/`: Airflow DAG definitions (example pipelines and executor tests).
- `airflow/plugins/`: Airflow plugins and shared operators/hooks.
- `requirements/`: Dependency source and lock files.
  - `requirements/base.in` and `requirements/dev.in`: Human-maintained inputs.
  - `requirements/base.txt` and `requirements/dev.txt`: `uv pip compile`-generated pinned lock files.
- `airflow/requirements.txt`: Airflow runtime wrapper (`-r ../requirements/base.txt`).
- `.devcontainer/requirements.txt`: Devcontainer/test wrapper (`-r ../requirements/dev.txt`).
- `infra/`: Infrastructure configuration.
  - `infra/terraform/aws/` and `infra/terraform/k8/`: Terraform for AWS/localstack and Kubernetes.
  - `infra/airflow-values.yaml`: Helm values for the Airflow chart.
- `.devcontainer/`: Local bootstrap and port-forwarding scripts for the devcontainer workflow.

## Build, Test, and Development Commands
- `make kube-info`: Switch to the `local-datalab` context and list namespaces/pods/cronjobs.
- `make port-forward` or `make port-forward-manager`: Forward Airflow API and Localstack ports.
- `make sync-dags`: Sync `./airflow` to the Localstack S3 DAGs bucket.
- `make list-dags`: Inspect the Localstack S3 DAGs bucket.
- `bash .devcontainer/bootstrap.sh`: Provision Minikube, apply Terraform, and start port-forwards.
- `terraform fmt -check` / `terraform validate`: Run in `infra/terraform/aws` and `infra/terraform/k8`.
- `make lock-requirements`: Recompile pinned lock files from `requirements/*.in`.
- `make lint`: Run Ruff lint checks for Python code.
- `make format`: Run Ruff formatter for Python code.
- `make precommit-install` and `make precommit-run`: Install and run pre-commit hooks.
- `python -m pytest airflow/tests/test_dags/ -v` and `python -m pytest airflow/tests/test_plugins/ -v`: Run DAG and plugin tests.

## Coding Style & Naming Conventions
- Python: 4-space indentation; keep DAG IDs and task IDs in snake_case (see `airflow/dags/*.py`).
- Use Ruff for linting/formatting, configured in `pyproject.toml`.
- Run pre-commit hooks before opening a PR (`.pre-commit-config.yaml`).
- Terraform: 2-space indentation; run `terraform fmt` before committing.
- Naming: DAG file names should describe the domain (e.g., `ingest_satellite_raster.py`).

## Testing Guidelines
- Frameworks: `pytest` and `pytest-mock` (installed via `requirements/dev.txt`; see `.github/workflows/python-test.yaml`).
- Placement: add tests under `airflow/tests/test_dags/` and `airflow/tests/test_plugins/` using `test_*.py`.
- Scope: new DAGs and plugins should include at least a basic import/parse test.

## Dependency Management
- Edit `requirements/base.in` and `requirements/dev.in`; do not hand-edit `requirements/base.txt` or `requirements/dev.txt`.
- After dependency changes, run `make lock-requirements` and commit both `.in` and `.txt` updates.

## Commit & Pull Request Guidelines
- Commit messages use an imperative verb + concise description (e.g., “Refactor Airflow DAGs sync CronJob YAML path”).
- PRs should include: what/why summary, linked issue if applicable, and commands run.
- For infra changes, include evidence of `terraform fmt -check` and `terraform validate`.

## Configuration & Secrets
- Environment defaults live in `.env` (e.g., `TF_VAR_aws_region`, `AWS_ENDPOINT_URL`).
- Treat `.env` as local-only; do not commit real credentials or production endpoints.
