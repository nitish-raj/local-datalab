from __future__ import annotations

import json
import os
from datetime import datetime

from airflow.sdk import dag, task, get_current_context
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from pystac_client import Client
from plugins.s3_utils import s3_local, parse_s3
import planetary_computer as pc


def pick_asset(item, candidates):
    keys = list(item.assets.keys())
    for c in candidates:
        if c in item.assets:
            return item.assets[c].href
    for c in candidates:
        for k in keys:
            if c.lower() == k.lower():
                return item.assets[k].href
    raise KeyError(f"Missing asset {candidates}. Available: {keys[:80]}")


@dag(
    dag_id="ingest_sentinel2_data",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["ingest", "sentinel2"],
)
def ingest_sentinel2_data():
    @task
    def get_conf() -> dict:
        ctx = get_current_context()
        return ctx["dag_run"].conf or {}

    @task
    def ingest(conf: dict, day: str) -> dict:
        processed_bucket = conf["processed_bucket"]
        out_prefix = conf["aoi_out_prefix"].rstrip("/") + "/"

        bkt, key = parse_s3(conf["aois_json_s3"])
        s3 = s3_local()
        aois = json.loads(s3.get_object(Bucket=bkt, Key=key)["Body"].read().decode())

        stac_url = os.environ.get(
            "STAC_URL", "https://planetarycomputer.microsoft.com/api/stac/v1"
        )
        collection = os.environ.get("STAC_COLLECTION", "sentinel-2-l2a")
        max_cloud = float(os.environ.get("MAX_CLOUD", "30"))
        dt = f"{day}T00:00:00Z/{day}T23:59:59Z"

        cat = Client.open(stac_url)
        wrote = []

        for a in aois:
            aoi_id = a["aoi_id"]
            bbox = a["bbox"]

            search = cat.search(
                collections=[collection],
                bbox=bbox,
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
                    "bbox": bbox,
                }
            else:
                items.sort(
                    key=lambda it: (
                        it.properties.get("eo:cloud_cover", 999.0),
                        it.properties.get("datetime", ""),
                    )
                )
                item = items[0]
                try:
                    item = pc.sign(item)
                except Exception:
                    pass

                payload = {
                    "aoi_id": aoi_id,
                    "date": day,
                    "status": "ok",
                    "bbox": bbox,
                    "item_datetime": item.properties.get("datetime"),
                    "cloud_cover": item.properties.get("eo:cloud_cover"),
                    "b04_href": pick_asset(item, ["B04", "B04_10m", "red"]),
                    "b08_href": pick_asset(item, ["B08", "B08_10m", "nir"]),
                }

            out_key = f"{out_prefix}ingest/date={day}/aoi_id={aoi_id}/s2_refs.json"
            s3.put_object(
                Bucket=processed_bucket,
                Key=out_key,
                Body=json.dumps(payload).encode(),
                ContentType="application/json",
            )
            wrote.append(f"s3://{processed_bucket}/{out_key}")

        return {
            "processed_bucket": processed_bucket,
            "aoi_out_prefix": out_prefix,
            "fields_with_aoi_s3": conf["fields_with_aoi_s3"],
            "date": day,
            "s2_refs": wrote,
        }

    conf = get_conf()
    day = "{{ macros.ds_add(ds, -1) }}"
    payload = ingest(conf, day)

    TriggerDagRunOperator(
        task_id="trigger_calculate_daily_ndvi",
        trigger_dag_id="calculate_daily_ndvi",
        conf=payload,
        wait_for_completion=False,
        reset_dag_run=True,
    )


ingest_sentinel2_data()
