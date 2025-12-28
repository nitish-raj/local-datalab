from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from airflow.sdk import dag, task, get_current_context
import rasterio
from rasterio.mask import mask
from plugins.s3_utils import s3_local, read_gdf_from_s3


def read_masked_band(href: str, geom4326):
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS="tif"
    ):
        with rasterio.open(href) as src:
            geom_src = (
                gpd.GeoSeries([geom4326], crs="EPSG:4326").to_crs(src.crs).iloc[0]
            )
            out, _ = mask(src, [geom_src], crop=True)
            arr = out[0].astype("float32")
            if src.nodata is not None:
                arr[arr == src.nodata] = np.nan
            return arr, src.crs.to_string()


@dag(
    dag_id="calculate_daily_ndvi",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dynamic", "fields", "daily"],
)
def calculate_daily_ndvi():
    @task
    def get_conf() -> dict:
        ctx = get_current_context()
        return ctx["dag_run"].conf or {}

    @task
    def build_field_work(conf: dict, day: str) -> list[dict]:
        day = conf.get("date", day)
        fields_gdf = read_gdf_from_s3(conf["fields_with_aoi_s3"])

        for col in ["planting_date", "aoi_id"]:
            if col not in fields_gdf.columns:
                raise ValueError(f"fields_with_aoi.geojson must contain '{col}'")

        if "field_id" not in fields_gdf.columns:
            fields_gdf["field_id"] = [f"F{i+1:03d}" for i in range(len(fields_gdf))]

        fields_gdf["planting_date"] = gpd.pd.to_datetime(
            fields_gdf["planting_date"]
        ).dt.date
        run_day = gpd.pd.to_datetime(day).date()

        eligible = fields_gdf[fields_gdf["planting_date"] <= run_day].copy()
        if eligible.empty:
            return []

        work = []
        for _, r in eligible.iterrows():
            work.append(
                {
                    "field_id": r["field_id"],
                    "aoi_id": r["aoi_id"],
                    "planting_date": r["planting_date"].isoformat(),
                    "geom": r.geometry.__geo_interface__,
                }
            )
        return work

    @task
    def compute_field_ndvi(item: dict, conf: dict, day: str) -> dict:
        s3 = s3_local()

        processed_bucket = conf["processed_bucket"]
        out_prefix = conf["aoi_out_prefix"]
        day = conf.get("date", day)

        aoi_id = item["aoi_id"]
        field_id = item["field_id"]

        refs_key = (
            f"{out_prefix.rstrip('/')}/ingest/date={day}/aoi_id={aoi_id}/s2_refs.json"
        )
        try:
            refs_obj = s3.get_object(Bucket=processed_bucket, Key=refs_key)
            refs = json.loads(refs_obj["Body"].read().decode("utf-8"))
        except s3.exceptions.NoSuchKey:
            return {
                "field_id": field_id,
                "aoi_id": aoi_id,
                "date": day,
                "planting_date": item["planting_date"],
                "status": "no_satellite_item",
                "mean_ndvi": None,
            }

        if refs.get("status") != "ok":
            return {
                "field_id": field_id,
                "aoi_id": aoi_id,
                "date": day,
                "planting_date": item["planting_date"],
                "status": "no_satellite_item",
                "mean_ndvi": None,
            }

        geom = shape(item["geom"])
        red, _ = read_masked_band(refs["b04_href"], geom)
        nir, _ = read_masked_band(refs["b08_href"], geom)

        h = min(red.shape[0], nir.shape[0])
        w = min(red.shape[1], nir.shape[1])
        red = red[:h, :w]
        nir = nir[:h, :w]

        den = nir + red
        ndvi = np.where(den != 0, (nir - red) / den, np.nan)
        mean_ndvi = float(np.nanmean(ndvi)) if np.isfinite(ndvi).any() else None

        return {
            "field_id": field_id,
            "aoi_id": aoi_id,
            "date": day,
            "planting_date": item["planting_date"],
            "status": "ok",
            "mean_ndvi": mean_ndvi,
            "cloud_cover": refs.get("cloud_cover"),
            "item_datetime": refs.get("item_datetime"),
        }

    @task
    def write_daily_outputs(results, conf: dict, day: str) -> str:
        s3 = s3_local()

        processed_bucket = conf["processed_bucket"]
        out_prefix = conf["aoi_out_prefix"]
        day = conf.get("date", day)

        results = list(results)

        base = f"{out_prefix.rstrip('/')}/field_timeseries/date={day}/"
        # 1) consolidated output for the day
        consolidated_key = f"{base}fields_ndvi.json"
        s3.put_object(
            Bucket=processed_bucket,
            Key=consolidated_key,
            Body=json.dumps({"date": day, "records": results}).encode("utf-8"),
            ContentType="application/json",
        )

        # 2) per-field daily point output
        for r in results:
            fid = r["field_id"]
            key = f"{base}field_id={fid}/ndvi.json"
            s3.put_object(
                Bucket=processed_bucket,
                Key=key,
                Body=json.dumps(r).encode("utf-8"),
                ContentType="application/json",
            )

        return f"s3://{processed_bucket}/{consolidated_key}"

    conf = get_conf()
    day = "{{ ds }}"
    work = build_field_work(conf, day)
    results = compute_field_ndvi.partial(conf=conf, day=day).expand(item=work)
    write_daily_outputs(results, conf, day)


calculate_daily_ndvi()
