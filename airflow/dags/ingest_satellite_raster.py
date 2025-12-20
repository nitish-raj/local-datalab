from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id="ingest_satellite_raster",
    start_date=datetime(2025, 12, 1),
    catchup=False,
    tags=["example"],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    start >> end
