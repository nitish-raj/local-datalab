from __future__ import annotations

from datetime import datetime

import pandas as pd
from airflow.sdk import dag, task, get_current_context
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from shapely.geometry import shape

from domain.models import AoiWorkItem, NdviResult, PipelineConf
from domain.paths import ndvi_day_prefix
from repositories.artifact_repo import (
    ingest_ref_exists,
    ndvi_payload,
    ndvi_exists,
    read_fields_with_aoi,
    read_ingest_ref,
    write_ndvi_result,
)
from services.ndvi_service import compute_ndvi_for_aoi


def _no_satellite_item(aoi_id: str, day: str) -> dict:
    return ndvi_payload(
        NdviResult(
            aoi_id=aoi_id,
            date=day,
            status="no_satellite_item",
            mean_ndvi=None,
            cloud_cover=None,
            item_datetime=None,
        )
    )


def _serialize_aoi_work(aoi_id: str, geometry) -> dict:
    return AoiWorkItem(aoi_id=aoi_id, geom=geometry.__geo_interface__).to_dict()


def _parse_conf(raw_conf: dict) -> dict:
    try:
        conf = PipelineConf.from_dict(raw_conf).to_dict()
        conf.update({k: v for k, v in raw_conf.items() if k not in conf})
        return conf
    except KeyError:
        return raw_conf


@dag(
    dag_id="03_calculate_daily_ndvi",
    start_date=datetime(2025, 12, 1),
    catchup=False,
    default_args={"retries": 3},
    tags=["dynamic", "fields", "daily"],
)
def calculate_daily_ndvi():
    @task
    def get_conf() -> dict:
        ctx = get_current_context()
        return _parse_conf(ctx["dag_run"].conf or {})

    @task
    def build_aoi_work(conf: dict, day: str) -> list[dict]:
        conf_data = _parse_conf(conf)
        day = conf_data.get("date", day)
        fields_gdf = read_fields_with_aoi(conf_data["fields_with_aoi_s3"])

        for col in ["planting_date", "aoi_id"]:
            if col not in fields_gdf.columns:
                raise ValueError(f"fields_with_aoi.geojson must contain '{col}'")

        fields_gdf["planting_date"] = pd.to_datetime(
            fields_gdf["planting_date"]
        ).dt.date
        run_day = pd.to_datetime(day).date()

        # Only include fields planted on or before the run day.
        eligible = fields_gdf[fields_gdf["planting_date"] <= run_day].copy()
        if eligible.empty:
            return []

        processed_bucket = conf_data["processed_bucket"]
        ingest_prefix = conf_data["ingest_out_prefix"]
        calc_prefix = conf_data["calc_out_prefix"]

        work = []
        for aoi_id, group in eligible.groupby("aoi_id"):
            aoi_id = str(aoi_id)
            if ndvi_exists(processed_bucket, calc_prefix, aoi_id, day):
                continue
            if not ingest_ref_exists(processed_bucket, ingest_prefix, aoi_id, day):
                continue
            geoms = group.geometry
            try:
                geom = geoms.union_all()
            except AttributeError:
                geom = geoms.unary_union
            work.append(_serialize_aoi_work(aoi_id, geom))
        return work

    @task(max_active_tis_per_dag=2)
    def compute_aoi_ndvi(item: dict, conf: dict, day: str) -> dict:
        conf_data = _parse_conf(conf)
        processed_bucket = conf_data["processed_bucket"]
        ingest_prefix = conf_data["ingest_out_prefix"]
        day = conf_data.get("date", day)

        aoi = AoiWorkItem.from_dict(item)
        try:
            if not ingest_ref_exists(processed_bucket, ingest_prefix, aoi.aoi_id, day):
                return _no_satellite_item(aoi.aoi_id, day)
            ref = read_ingest_ref(processed_bucket, ingest_prefix, aoi.aoi_id, day)
        except Exception:
            return _no_satellite_item(aoi.aoi_id, day)

        if ref.status != "ok":
            return _no_satellite_item(aoi.aoi_id, day)

        result = compute_ndvi_for_aoi(shape(aoi.geom), ref)
        return ndvi_payload(result)

    @task
    def write_daily_outputs(results, conf: dict, day: str) -> str:
        conf_data = _parse_conf(conf)
        processed_bucket = conf_data["processed_bucket"]
        calc_prefix = conf_data["calc_out_prefix"]
        day = conf_data.get("date", day)

        results = list(results)

        aoi_base = ndvi_day_prefix(calc_prefix, day)
        for r in results:
            write_ndvi_result(
                bucket=processed_bucket,
                calc_prefix=calc_prefix,
                result=NdviResult.from_dict(r),
            )

        if results:
            return f"s3://{processed_bucket}/{aoi_base}aoi_id={results[0]['aoi_id']}/ndvi.json"
        return ""

    conf = get_conf()
    day = "{{ ds }}"
    work = build_aoi_work(conf, day)
    results = compute_aoi_ndvi.partial(conf=conf, day=day).expand(item=work)
    write_done = write_daily_outputs(results, conf, day)

    trigger_postgres_sync = TriggerDagRunOperator(
        task_id="trigger_sync_ndvi_to_postgres",
        trigger_dag_id="04_sync_ndvi_to_postgres",
        conf=conf,
        wait_for_completion=False,
        reset_dag_run=True,
    )

    write_done >> trigger_postgres_sync


calculate_daily_ndvi()
