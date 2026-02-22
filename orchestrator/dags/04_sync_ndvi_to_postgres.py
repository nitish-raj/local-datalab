from __future__ import annotations

import os
from datetime import datetime

from airflow.sdk import dag, get_current_context, task

from domain.models import PipelineConf
from loaders.s3_to_postgres import (
    PostgresConfig,
    sync_ndvi_from_s3_to_postgres,
)


def _parse_conf(raw_conf: dict) -> dict:
    try:
        conf = PipelineConf.from_dict(raw_conf).to_dict()
        conf.update({k: v for k, v in raw_conf.items() if k not in conf})
        return conf
    except KeyError:
        return raw_conf


@dag(
    dag_id="04_sync_ndvi_to_postgres",
    schedule=None,
    start_date=datetime(2025, 12, 1),
    catchup=False,
    default_args={"retries": 2},
    tags=["warehouse", "postgres", "ndvi"],
)
def sync_ndvi_to_postgres():
    @task
    def load_day_partition() -> dict[str, int]:
        context = get_current_context()
        conf = _parse_conf(context["dag_run"].conf or {})
        return sync_ndvi_from_s3_to_postgres(
            bucket=conf.get("processed_bucket", os.environ["PROCESSED_AOI_BUCKET"]),
            calc_prefix=conf.get("calc_out_prefix", "calculation/"),
            day=conf.get("date"),
            postgres_config=PostgresConfig.from_env(),
        )

    load_day_partition()


sync_ndvi_to_postgres()
