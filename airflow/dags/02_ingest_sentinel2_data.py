from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from airflow.sdk import dag, task, get_current_context
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from pystac_client import Client
import planetary_computer as pc
import pandas as pd
from utils.s3_utils import (
    parse_s3,
    get_s3_object,
    write_to_s3,
    read_gdf_from_s3,
    s3_object_exists,
)


def pick_asset_id(item, candidates):
    keys = list(item.assets.keys())
    for c in candidates:
        if c in item.assets:
            return c
    for c in candidates:
        for k in keys:
            if c.lower() == k.lower():
                return k
    raise KeyError(f"Missing asset {candidates}. Available: {keys[:80]}")


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
        return ctx["dag_run"].conf or {}

    @task
    def build_days(conf: dict) -> list[str]:
        fields_gdf = read_gdf_from_s3(conf["fields_with_aoi_s3"])
        if "planting_date" not in fields_gdf.columns:
            raise ValueError("fields_with_aoi.geojson must contain 'planting_date'")

        fields_gdf["planting_date"] = pd.to_datetime(
            fields_gdf["planting_date"]
        ).dt.date
        start_day = fields_gdf["planting_date"].dropna().min()
        end_day = datetime.now(timezone.utc).date()

        if start_day is None or pd.isna(start_day):
            return []

        bkt, key = parse_s3(conf["aois_json_s3"])
        aois = json.loads(get_s3_object(bucket=bkt, key=key))
        processed_bucket = conf["processed_bucket"]
        ingest_prefix = conf["ingest_out_prefix"].rstrip("/") + "/"

        days = []
        current_day = start_day
        while current_day <= end_day:
            day_str = current_day.isoformat()
            all_exist = True
            for aoi in aois:
                aoi_id = aoi["aoi_id"]
                out_key = f"{ingest_prefix}aoi_id={aoi_id}/date={day_str}/s2_refs.json"
                if not s3_object_exists(processed_bucket, out_key):
                    all_exist = False
                    break
            if not all_exist:
                days.append(day_str)
            current_day += timedelta(days=1)
        return days

    @task
    def ingest(conf: dict, day: str) -> dict:
        processed_bucket = conf["processed_bucket"]
        out_prefix = conf["ingest_out_prefix"].rstrip("/") + "/"

        bkt, key = parse_s3(conf["aois_json_s3"])
        aois = json.loads(get_s3_object(bucket=bkt, key=key))

        stac_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
        collection = "sentinel-2-l2a"

        max_cloud = float(os.environ.get("MAX_CLOUD", "30"))

        dt = f"{day}T00:00:00Z/{day}T23:59:59Z"

        cat = Client.open(
            stac_url,
            modifier=pc.sign_inplace,
        )
        wrote = []

        for aoi in aois:
            aoi_id = aoi["aoi_id"]
            aoi_bbox = aoi["bbox"]
            out_key = f"{out_prefix}aoi_id={aoi_id}/date={day}/s2_refs.json"

            if s3_object_exists(processed_bucket, out_key):
                wrote.append(f"s3://{processed_bucket}/{out_key}")
                continue

            search = cat.search(
                collections=[collection],
                bbox=aoi_bbox,
                datetime=dt,
                query={"eo:cloud_cover": {"lt": max_cloud}},
                max_items=50,
            )
            items = list(search.items())

            if not items:
                payload = {
                    "aoi_id": aoi_id,
                    "date": day,
                    "status": "no_items",
                    "bbox": aoi_bbox,
                }
            else:
                items.sort(
                    key=lambda it: (
                        it.properties.get("eo:cloud_cover", 999.0),
                        it.properties.get("datetime", ""),
                    )
                )
                item = items[0]

                payload = {
                    "aoi_id": aoi_id,
                    "date": day,
                    "status": "ok",
                    "bbox": aoi_bbox,
                    "item_datetime": item.properties.get("datetime"),
                    "cloud_cover": item.properties.get("eo:cloud_cover"),
                    "stac_url": stac_url,
                    "collection": collection,
                    "item_id": item.id,
                    "b04_asset": pick_asset_id(item, ["B04", "B04_10m", "red"]),
                    "b08_asset": pick_asset_id(item, ["B08", "B08_10m", "nir"]),
                }

            write_to_s3(
                bucket=processed_bucket,
                key=out_key,
                data=json.dumps(payload).encode(),
                content_type="application/json",
            )
            wrote.append(f"s3://{processed_bucket}/{out_key}")

        return {
            "processed_bucket": processed_bucket,
            "ingest_out_prefix": out_prefix,
            "calc_out_prefix": conf["calc_out_prefix"],
            "fields_with_aoi_s3": conf["fields_with_aoi_s3"],
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
