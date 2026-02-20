from __future__ import annotations

import os
import tempfile
from datetime import datetime

import geopandas as gpd
import pandas as pd
from airflow.sdk import dag, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from domain.models import PipelineConf
from domain.paths import aois_key, fields_with_aoi_key
from repositories.artifact_repo import write_aois, write_fields_with_aoi
from services.aoi_service import infer_aois_and_tag_fields
from utils.s3_utils import download_s3_to_file


@dag(
    dag_id="01_simulate_aoi_from_fields",
    schedule=None,
    start_date=datetime(2025, 12, 1),
    catchup=False,
    default_args={"retries": 3},
    tags=["aoi", "fields", "simulation"],
)
def simulate_aoi_from_fields():
    @task
    def build_and_upload() -> dict:
        raw_bucket = os.environ["RAW_SATELLITE_BUCKET"]
        fields_key = "fields.geojson"

        processed_bucket = os.environ["PROCESSED_AOI_BUCKET"]
        derived_prefix = "derived/".rstrip("/") + "/"
        ingest_prefix = "ingest/".rstrip("/") + "/"
        calc_prefix = "calculation/".rstrip("/") + "/"

        tmpdir = tempfile.mkdtemp(prefix="aoi_")
        fields_path = os.path.join(tmpdir, "fields.geojson")
        download_s3_to_file(raw_bucket, fields_key, fields_path)
        fields_gdf = gpd.read_file(fields_path)

        aois, fields_with_aoi = infer_aois_and_tag_fields(
            fields_gdf,
            min_cluster_size=2,
            eps_quantile=0.90,
            padding_m=2000,
        )

        aois_json_key = aois_key(derived_prefix)
        fields_with_aoi_artifact_key = fields_with_aoi_key(derived_prefix)

        write_aois(processed_bucket, aois_json_key, aois)

        for col in fields_with_aoi.columns:
            if pd.api.types.is_datetime64_any_dtype(fields_with_aoi[col]):
                fields_with_aoi[col] = fields_with_aoi[col].dt.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )

        write_fields_with_aoi(
            processed_bucket,
            fields_with_aoi_artifact_key,
            fields_with_aoi,
        )

        conf_payload = PipelineConf(
            processed_bucket=processed_bucket,
            derived_out_prefix=derived_prefix,
            ingest_out_prefix=ingest_prefix,
            calc_out_prefix=calc_prefix,
            aois_json_s3=f"s3://{processed_bucket}/{aois_json_key}",
            fields_with_aoi_s3=(
                f"s3://{processed_bucket}/{fields_with_aoi_artifact_key}"
            ),
        ).to_dict()
        conf_payload["aois_count"] = len(aois)
        return conf_payload

    payload = build_and_upload()

    TriggerDagRunOperator(
        task_id="trigger_ingest_sentinel2_data",
        trigger_dag_id="02_ingest_sentinel2_data",
        conf=payload,
        wait_for_completion=False,
        reset_dag_run=True,
    )


simulate_aoi_from_fields()
