# Repository Guidelines

## Project Structure & Module Organization
- `orchestrator/dags/`: Airflow DAG definitions (orchestration-only modules).
- `src/`: Pipeline code for shared logic.
  - `domain/`: Typed payload contracts and S3 key builders.
  - `services/`: Domain/business logic extracted from DAG files.
  - `repositories/`: Artifact persistence/idempotency wrappers over low-level S3 utils.
  - `loaders/`: Cross-system loaders (e.g., S3 to Postgres raw ingestion).
- `tests/`: Unit/integration tests for dags, domain, services, repositories, plugins, and loaders.
- `transform/`: dbt project for SQL transformations in analytics Postgres.
- `requirements/`: Dependency source and lock files.
  - `requirements/base.in` and `requirements/dev.in`: Human-maintained inputs.
  - `requirements/base.txt` and `requirements/dev.txt`: `uv pip compile`-generated pinned lock files.
- `orchestrator/requirements.txt`: Airflow runtime wrapper (`-r ../requirements/base.txt`).
- `.devcontainer/requirements.txt`: Devcontainer/test wrapper (`-r ../requirements/dev.txt`).
- `infra/`: Infrastructure configuration.
  - `infra/terraform/aws/` and `infra/terraform/k8/`: Terraform for AWS/localstack and Kubernetes.
  - `infra/airflow-values.yaml`: Helm values for the Airflow chart.
- `.devcontainer/`: Local bootstrap and port-forwarding scripts for the devcontainer workflow.

## Build, Test, and Development Commands
- `make kube-info`: Switch to the `local-datalab` context and list namespaces/pods/cronjobs.
- `make port-forward` or `make port-forward-manager`: Forward Airflow API, Localstack, and analytics Postgres ports.
- `make sync-dags`: Sync DAG files and `src` package modules to the Localstack S3 DAGs bucket.
- `make list-dags`: Inspect the Localstack S3 DAGs bucket.
- `bash .devcontainer/bootstrap.sh`: Provision Minikube, apply Terraform, and start port-forwards.
- `terraform fmt -check` / `terraform validate`: Run in `infra/terraform/aws` and `infra/terraform/k8`.
- `make lock-requirements`: Recompile pinned lock files from `requirements/*.in`.
- `make lint`: Run Ruff lint checks for Python code.
- `make format`: Run Ruff formatter for Python code.
- `make precommit-install` and `make precommit-run`: Install and run pre-commit hooks.
- `make sync-ndvi-postgres`: Load NDVI artifacts from S3 into Postgres raw table.
- `make dbt-debug`, `make dbt-run`, `make dbt-test`: Run dbt for warehouse transformations.
- `PYTHONPATH=src python -m pytest tests/test_dags/ -v` and `PYTHONPATH=src python -m pytest tests/test_plugins/ -v`: Run DAG and plugin tests.

## Coding Style & Naming Conventions
- Python: 4-space indentation; keep DAG IDs and task IDs in snake_case (see `orchestrator/dags/*.py`).
- Use Ruff for linting/formatting, configured in `pyproject.toml`.
- Run pre-commit hooks before opening a PR (`.pre-commit-config.yaml`).
- Terraform: 2-space indentation; run `terraform fmt` before committing.
- Naming: DAG file names should describe the domain (e.g., `ingest_satellite_raster.py`).

## Testing Guidelines
- Frameworks: `pytest` and `pytest-mock` (installed via `requirements/dev.txt`; see `.github/workflows/python-test.yaml`).
- Placement:
  - `tests/test_dags/`: DAG import/parse and DAG-specific behavior tests.
  - `tests/test_plugins/`: low-level utility/plugin tests.
  - `tests/test_domain/`: model/path contract tests.
  - `tests/test_services/`: service-layer unit tests.
  - `tests/test_repositories/`: repository serialization/idempotency tests.
  - `tests/test_loaders/`: cross-system loader tests (S3 to Postgres).
- Scope: new DAGs and plugins should include at least a basic import/parse test.

## Architecture Responsibilities
- DAG modules should focus on orchestration (task order, mapping, triggering).
- Service modules should own compute/business logic.
- Repository modules should own storage access, content types, and idempotency checks.
- Domain modules should own data shape and key conventions.

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
