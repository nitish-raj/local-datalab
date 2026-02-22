<div align="center">
  <img src="icon.png" width="100px" alt="Local DataLab" />
  <h1>Local Data Lab</h1>

  <p>Local Data Lab is a containerized, local-first data platform based on Airflow and Localstack (AWS) on Minikube (k8) with IaC using Terraform.</p>

  <p>
    <img src="https://img.shields.io/static/v1?label=Dev+Containers&message=Spec&color=0A7EA4&labelColor=1B1B1B" alt="Dev Containers">
    <img src="https://img.shields.io/badge/Apache%20Airflow-017CEE?logo=apacheairflow&logoColor=fff" alt="Airflow">
    <img src="https://img.shields.io/badge/LocalStack-23B0A6?logo=localstack&logoColor=white" alt="LocalStack">
    <img src="https://img.shields.io/badge/Minikube-2B6CB0?logo=minikube&logoColor=white" alt="Minikube">
    <img src="https://img.shields.io/badge/Kubernetes-326CE5?&style=plastic&logo=kubernetes&logoColor=white" alt="Kubernetes">
    <img src="https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white" alt="Terraform">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  </p>
  <a href="https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml">
    <img src="https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml/badge.svg" alt="terraform-validate">
  </a>
  <a href="https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml">
    <img src="https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml/badge.svg" alt="python-test">
  </a>

</div>

> [!NOTE]
> This repo is designed to run with **Dev Containers**.
> You can use any IDE/editor that supports the Dev Container specification.
> If you do not use Dev Containers, additional host-specific setup is required (macOS, Linux, or Windows).

## System Requirements
- macOS, Linux, or Windows (with WSL2) capable of running Docker
- 4 CPU cores minimum (8 recommended for smoother Minikube + Localstack)
- 8 GB RAM minimum (16 GB recommended)
- 10+ GB free disk space for images, caches, and Terraform providers
- Hardware virtualization enabled (required by Docker Desktop/WSL2)

## Prerequisites
- `Docker Desktop`
  - Install: https://docs.docker.com/get-docker/
  - Must allow privileged containers and bind-mounting the repo directory
- A Dev Container-compatible IDE/editor
- `Git`
- Network access to pull images and features from Docker Hub/GHCR and Terraform providers
- A local `.env` file at repo root
  - Use the existing `.env` as a template and replace values for your environment as needed

## How to Run in a Dev Container
1. Open this repo in your Dev Container-compatible IDE/editor.
2. Reopen/rebuild the workspace in container mode from your IDE's Dev Container workflow.
3. The container build will run `.devcontainer/bootstrap.sh` on first start; it provisions Minikube, applies Terraform, and starts port forwards. This may take 10-20 minutes depending on system resources and network speed.
4. After the container starts, access services:
   - Airflow UI: http://localhost:8080 (default user: `admin`, password: `admin`)
       - Trigger first DAG with prefix `01_`, it will auto trigger subsequent DAGs `02_`, `03_`, and `04_`
   - Localstack: It does not have a UI, but you can interact with it using AWS CLI or SDKs at `http://localhost:4566`. For example, list S3 buckets with:
      ```
      aws --endpoint-url=http://localhost:4566 s3 ls
      ```
   - Analytics Postgres: available locally at `localhost:5432`
   - Minikube Dashboard: Run `minikube dashboard -p local-datalab --url` in the container terminal to get the URL.


## Architecture Diagram
![Infra Architecture](https://mermaid.ink/svg/pako:eNqlWG1v2zYQ_iuE-qE2RiWSJcu22hVI423NlhZZ3BdgdRHQEmkLlkWDpGKndf_7SL1QlC0HA5ZPIe-ee7_jyT-siMbYCi3btudZRDOSLMN5BgBJ6S5aISaKEwArsUlv0QKnPASC5VjdpuiJ5iIEOF2ro1jhDQ7BAnGsj58RS9AixbwSQ2gmZsl3yeb62_08K9RqXeD2XrHxfLFkaLsCU_woTRIoyTB7S_df59ZrvkUZ4OIpxb--VMJsrqS5wXb_qhBu73CyXIkwcJyXb0w86H2egWvpLPgFTGm0xqz_-lJJezO3vpXGxQnDkUhoVthR3pm23GIipA22BpiQj2_ru4rzKotWlPV6oN8Pw7CMVc3yETOGCGUbKY6gkCBbpaG5Br0kIwxdivqib-i8pRFKp2jJNZjQNJYeTq_-4KB3cYkSpkJqYq4Zzd5RLhp9qYwBUFcFTcJiI1iX_CmL7FjquOCrTt3Att8cFBfgNGcRPmgVJSvO4pMQvk-yZJ0v8HWac-nZM-kcdqazxoNKwHH-jjNY3tWo5_KhTfwwmyKBnrHM77TsA9pgCYgwiCXcTtHi1LbuYqlCygWK1rPHSOcH72VHZEtso1SAGWaPiRSeatbQHwZBS3gj5o7GTZpVuBoSkLRzqM_XX3slaBXHhip7-xj1v9XJbEVr5r3NZScJVYmGkpkHqvuWru70qL97tNMWIxatkkcMGNo9cCRwmiYCPywKeUfi7hiNMOc4PgFva8oDokk3WBVxaeUJuuqfB1X_XWCjtk8SWPTF1Rc5am5vwKUKxdXdzaGdnTNJU9AmpM8wHeRB4EM7eTV_yzijrq9Kp_5HaVdh-e-VXal8h9NNuyArAlAUcI9TrJ4MU97VNlE1X8yIEseLowomKCmgV9kD0DapyP2WkFm0wnGeGkJkuGR4ECubqia3QLIsqrKiDY4kadmIkgo0uYX7Qtna1ETliCzvQO8v6TPLsMD8tz2OckGPDP3IkuUSMwO-oFKZvm4x38kRu2SY182qBo56cmvC7O_bftsfftTaVdyK8Q4krX8aeDlsnp9EtYwm9uHYGTvHoeTqUTh6c9TVn3TRMsNWL0kB7qyeojN0TZxnaVJ6lsXM73muMnPn6U1qzrLUeWq5VLtgOiTDeY6jSl5HSXeTTee6OaqS7KRpp7rJHZEs0tsaPOeefrkT3auZ8t_Wp4L1uff6jjLxO2U7xJrZz1AW001BklOsoIHjoqx8-HSjUcuUGgPp043BbCgp81WDDTdP9r2Cs71ylFztuzKCLU_rmDVLoBr1zewAspiKVYsfjjepEtjUU1WA2nxF11lpHr7yLfGAar5DK5_1_wXHjskXmB_Miqh3vVMJpeRSU5QizqeYgGKZBXKKpuELjElACOSC0TUOX3iL8YAEMKIpZeELh7ijAXrVAtdjvoSTERka8FHkIRzXcJe4rj9qw5tFpjaAECQ11hJcZzEZu9qAobc4NiDJZIgzlIISIgcWlx8rDD2FwAcerOxySEz8RmqAPB81UgfYDdpS1dw2_SJkJB2p8WQy8lwdFt9zfefIrzypkTEZkLFG4sgfTyYaiRzfx0cRKVqpRAvZNfI5ZzgTtQTzqpRi3BSS0iRbz9T6ANwxdCegA1iFapfEYhU6232nJG1VU_PwqLLh0SdgWUqNP-ZUgnp4Qj0noTkSYTn9oB50sB7SsOkdWJU51D1QFaChVC9pujYMYmsdhK3lDbY2NijXXqh3WGj0ZVOzhlyjn6EeRbIMDJa6LWHzmVaX2SsLWkuWxJYceinH0NpgtkHqbP1QAuZW8b0-t0L5b4wJylO59M6znxIn171_KN1Yofrwhxaj-XKl5eRbqQJPEyQHfcMipw1m1zTPhBW6g0KEFf6w9lZoB8HowvEHo6HnjQeu43jQerLCcXAxkBXvjf3hxJO0wU9ofS-Uuhf-0BkEQzeYuL4XjIIxtHCcyC3qffnTRfELxs9_AYUUgoM)

## Data Flow Diagram (DAGs + Pipeline)
![DAG Architecture](https://mermaid.ink/svg/pako:eNp9Vm1v2zYQ_isE82VDZccSFTtRX4CsxoYC2TokQT9sHgRaImUuFOmRVJ00zn_fkXqJ7DQFDJoU77l77vicqEdc6JLhDE8mk5UqtOKiylYKIS71rthQ48IKoY2r5RVdM2kz5EzD_FNJH3TjMsTknV-6DatZhtbUsmH5hRpB15LZzg3Xyt2Ib2AWp9v7lQphh1jo6tqb2WZdGbrdoKWgMKl_0fd_r_Dy8je0pI6iX8F8hf9pHQ62NwRsrnRBpXW0uIP1YIPQNd3BrqG73FLHpBSO5eumuGPu3dqcfuCCydKetn_Tiul_rVYj-J9GF8xaVoKTbT_PqRadk8GUqXKljogB71nc8Z_FGbKibiSwCHhudJ23cUfxlrP41kPWjZAQR5V5s5WaloGsUJwZdPn5k0VvkKMVOoK_xiHpOSQZEqpi1uWWKScUk0leQmEPCCSBQMVc7kVxtJUM3Er6YAOrWqiftpJ6f5X3xn5GTsMPDI7A_pza-AF4c3v5EVlGTbFB2zax05egGE0mH9rYw4z8OF_S50syBKoo2qKXVMiHXJVfxUEE8nq6ZJSuP7KdNneB-UG66N17ZBqVH1MnId9C19umO3IfO-CDTv0A51hTewd_fyy_fDqCpwDfGTFQh44DV_aYfVcVMtQHAg-z9EWloCH87r7UO-WVhQ61v28l2NqGabAOPFDJjPjKylNIxk69NRDvn7Vu8p1wG5_ss7-hhY593hpRVcwsaXXdqM-gAOq02beK7dkO4IAwDPiOg78aNOilD9hJZx9OSwoLL67-BAep7sfCCtMA-a9h5gEFpb4BrUpWOASVqO0r9m2dbJIbxjuWnbTDPwTqOtl3ga9jLsr30-n01HPzk-_Uq_f93Xr1btu6kR_UbUxq38qkj9ApprMTlQJcyJmCC2dfWKejXPsGE1qFfJyomQVNMNtnfpTSoMVCgvsl48gSOEgpsxPG-JzzyDqj71h2QtbnCZ9HhZbaZCczHi8S-vYAWYaXoIfyBT8bQRcFoazsoTGP43RxCHW-7zos5wsw7rH8YkHiIWxK4nR2hF3r-2coH4W9SCmQ7paTnSjdJou396-lMLrmvM_RBnRp9HyGlowx_laJQpeEkfgqjPd9g0Xh1RnGJIwkCi-LMCZhbJ-koRBvcYQrI0qccbhFWYRrZmrq1_jRe17hcKevcAbTknHaSLj6VuoJcFuq_tK6xpn_OIiw0U21Gfw0Wy_sLs3BBCTAzEfdKIezi-ABZ4_4HmeT-XwxnaXJ4oyQ8ySezUiEH3B2Pp8mcCTkPD27ILCXPEX4W4gZT9OzWTI_i-cXcUrmi_l5hFkpoDF-b79uwkfO0_-3adXl)

## Pipeline Code Architecture

The pipeline code follows a production-friendly structure that separates orchestration,
business logic, storage boundaries, and SQL transformations.

- **Orchestration (`orchestrator/dags/`)**
  - DAG files contain scheduling, dependency wiring, and cross-DAG triggers.
  - Task internals delegate to package modules under `src/`.

- **Python package (`src/`)**
  - `domain/`: typed contracts and canonical S3 path builders.
  - `services/`: AOI inference, STAC ingestion planning/search, NDVI compute logic.
  - `repositories/`: storage/idempotency boundaries for S3 artifacts.
  - `loaders/`: S3-to-Postgres raw loading jobs.

- **Transformation layer (`transform/`)**
  - dbt models transform `raw.raw_ndvi_observations` into staging/marts schemas in Postgres.

- **Infrastructure (`infra/`)**
  - Terraform resources for LocalStack, Airflow, and analytics Postgres in one place.

## How To Add a New Pipeline Step

1. Define or reuse data contracts in `src/domain/models.py`.
2. Add key/path builders in `src/domain/paths.py` for any new artifact layout.
3. Implement business logic in a `src/services/*.py` module.
4. Add repository methods in `src/repositories/artifact_repo.py` for new artifacts.
5. Wire the DAG task in `orchestrator/dags/` to call service + repository code (avoid inline storage/domain logic).
6. Add focused tests under:
   - `tests/test_domain/`
   - `tests/test_services/`
   - `tests/test_repositories/`
7. Run validation commands:
   - `PYTHONPATH=src python -m pytest tests/test_domain -v`
   - `PYTHONPATH=src python -m pytest tests/test_services -v`
   - `PYTHONPATH=src python -m pytest tests/test_repositories -v`
   - `PYTHONPATH=src python -m pytest tests/test_dags -v`

## DBT Workflow

1. Ensure port forwards are running (`make port-forward`), including Postgres on `localhost:5432`.
2. Sync NDVI artifacts from S3 into Postgres raw table:

   ```bash
   make sync-ndvi-postgres
   ```

3. Run dbt models and tests:

   ```bash
   make dbt-debug
   make dbt-run
   make dbt-test
   ```
