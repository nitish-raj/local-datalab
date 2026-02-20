from __future__ import annotations

import os
from datetime import datetime

from airflow.sdk import dag, task, get_current_context
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from domain.models import PipelineConf
from repositories.artifact_repo import (
    ingest_ref_exists,
    read_aois,
    read_fields_with_aoi,
    write_ingest_ref,
)
from services.planning_service import plan_missing_ingest_days
from services.stac_service import fetch_ingest_ref


@dag(
    dag_id="02_ingest_sentinel2_data",
    schedule=None,
    start_date=datetime(2025, 12, 1),
    catchup=False,
    default_args={"retries": 3},
    tags=["ingest", "sentinel2"],
)
def ingest_sentinel2_data():
    @task
    def get_conf() -> dict:
        ctx = get_current_context()
        raw_conf = ctx["dag_run"].conf or {}
        try:
            conf = PipelineConf.from_dict(raw_conf).to_dict()
            conf.update(
                {key: value for key, value in raw_conf.items() if key not in conf}
            )
            return conf
        except KeyError:
            return raw_conf

    @task
    def build_days(conf: dict) -> list[str]:
        try:
            pipeline_conf = PipelineConf.from_dict(conf)
            conf_data = pipeline_conf.to_dict()
        except KeyError:
            conf_data = conf

        fields_gdf = read_fields_with_aoi(conf_data["fields_with_aoi_s3"])
        aois = read_aois(conf_data["aois_json_s3"])
        return plan_missing_ingest_days(
            fields_with_aoi=fields_gdf,
            aois=aois,
            processed_bucket=conf_data["processed_bucket"],
            ingest_prefix=conf_data["ingest_out_prefix"],
            exists_fn=ingest_ref_exists,
        )

    @task
    def ingest(conf: dict, day: str) -> dict:
        try:
            pipeline_conf = PipelineConf.from_dict(conf)
            conf_data = pipeline_conf.to_dict()
        except KeyError:
            conf_data = conf

        processed_bucket = conf_data["processed_bucket"]
        out_prefix = conf_data["ingest_out_prefix"]

        aois = read_aois(conf_data["aois_json_s3"])

        stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        collection = "sentinel-2-l2a"

        max_cloud = float(os.environ.get("MAX_CLOUD", "30"))

        for aoi in aois:
            if ingest_ref_exists(processed_bucket, out_prefix, aoi.aoi_id, day):
                continue

            ref = fetch_ingest_ref(
                aoi=aoi,
                day=day,
                max_cloud=max_cloud,
                stac_url=stac_url,
                collection=collection,
            )

            write_ingest_ref(
                bucket=processed_bucket,
                ingest_prefix=out_prefix,
                ref=ref,
            )

        return {
            "processed_bucket": conf_data["processed_bucket"],
            "ingest_out_prefix": conf_data["ingest_out_prefix"],
            "calc_out_prefix": conf_data["calc_out_prefix"],
            "fields_with_aoi_s3": conf_data["fields_with_aoi_s3"],
            "date": day,
        }

    conf = get_conf()
    days = build_days(conf)
    payloads = ingest.partial(conf=conf).expand(day=days)

    TriggerDagRunOperator.partial(
        task_id="trigger_calculate_daily_ndvi",
        trigger_dag_id="03_calculate_daily_ndvi",
        wait_for_completion=False,
        reset_dag_run=True,
    ).expand(conf=payloads)


ingest_sentinel2_data()
