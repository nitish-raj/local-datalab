# DBT Layer

This project owns SQL transformations on top of the `raw.raw_ndvi_observations` table
that is loaded from S3 NDVI artifacts.

## Run locally

1. Ensure port forwards are active:
   - LocalStack: `localhost:4566`
   - Analytics Postgres: `localhost:5432`
2. Load S3 artifacts into Postgres raw table:

   ```bash
   make sync-ndvi-postgres
   ```

3. Run dbt:

   ```bash
   make dbt-debug
   make dbt-run
   make dbt-test
   ```
