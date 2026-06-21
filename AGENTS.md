# Agent Notes

Keep this file short. Add guidance only when a future agent would likely miss it from the code alone.

## Architecture Boundaries

- `orchestrator/dags/` should stay orchestration-only: task order, mapping, scheduling, and cross-DAG triggers. Put compute logic in `src/services/`, storage/idempotency in `src/repositories/`, payload contracts and S3 keys in `src/domain/`, and cross-system loads in `src/loaders/`.
- The numbered DAGs are intentional. Trigger `01_simulate_aoi_from_fields.py` first; downstream DAGs `02_`, `03_`, and `04_` are part of the same pipeline flow.
- `make sync-dags` uploads both `orchestrator/dags/*.py` and `src/**/*.py` into the LocalStack Airflow DAGs bucket. Keep imports compatible with that layout.
- dbt lives under `transform/` and expects profiles from `transform/profiles` via `DBT_PROFILES_DIR=transform/profiles`.

## Commands Agents Usually Need

- Run Python tests with `PYTHONPATH=src`, for example `PYTHONPATH=src python -m pytest tests/test_services -v`.
- Make targets exist for common focused checks: `make test-dags`, `make test-plugins`, `make test-loaders`, `make lint`, `make format`, `make dbt-debug`, `make dbt-run`, and `make dbt-test`.
- Terraform checks must be run from both `infra/terraform/aws` and `infra/terraform/k8`: `terraform fmt -check` and `terraform validate`.
- `make port-forward` forwards Airflow on `localhost:8080`, LocalStack on `localhost:4566`, and analytics Postgres on `localhost:5432`.
- `make sync-ndvi-postgres` runs `PYTHONPATH=src python -m loaders.s3_to_postgres`.

## Dependencies And Config

- Edit `requirements/base.in` and `requirements/dev.in`; do not hand-edit `requirements/base.txt` or `requirements/dev.txt`. Rebuild locks with `make lock-requirements`.
- Do not change environment variables, model/API settings, timeouts, token limits, or other configuration values unless the user explicitly asks.
- `.env` is local-only. Do not add real credentials, production endpoints, or secrets to tracked files.

## Style And Tests

- Ruff is configured in `pyproject.toml` for Python 3.13, line length 88, double quotes, and lint rules `E`/`F`.
- New or changed DAG behavior should include a DAG import/parse test under `tests/test_dags/`.
- Add tests next to the layer being changed: `tests/test_domain/`, `tests/test_services/`, `tests/test_repositories/`, `tests/test_loaders/`, or `tests/test_plugins/`.
