from __future__ import annotations

import json
from datetime import datetime
import pandas as pd
import numpy as np
from shapely.geometry import shape
from airflow.sdk import dag, task, get_current_context
from rasterio.errors import RasterioIOError
from rasterio.features import rasterize
from rasterio.transform import from_origin
from utils.s3_utils import (
    read_gdf_from_s3,
    get_s3_object,
    write_to_s3,
    s3_object_exists,
)
import planetary_computer as pc
from pystac_client import Client
import stackstac
import xarray as xr


def rasterize_geom_mask(data_stack: xr.DataArray, geom4326) -> xr.DataArray:
    x_coords = data_stack.x.values
    y_coords = data_stack.y.values
    if x_coords.size < 2 or y_coords.size < 2:
        mask = np.ones((y_coords.size, x_coords.size), dtype=bool)
        return xr.DataArray(
            mask, coords={"y": data_stack.y, "x": data_stack.x}, dims=("y", "x")
        )
    x_res = float(x_coords[1] - x_coords[0])
    y_res = float(y_coords[0] - y_coords[1])
    transform = from_origin(
        float(x_coords[0]), float(y_coords[0]), abs(x_res), abs(y_res)
    )

    # Rasterize polygon to a pixel mask so only AOI pixels are used for NDVI.
    mask = rasterize(
        [geom4326],
        out_shape=(y_coords.size, x_coords.size),
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
    ).astype(bool)
    return xr.DataArray(
        mask, coords={"y": data_stack.y, "x": data_stack.x}, dims=("y", "x")
    )


def pick_epsg(item, asset_keys: list[str]) -> int | None:
    # Prefer item-level EPSG; fall back to asset-level EPSG if needed.
    epsg = item.properties.get("proj:epsg")
    if isinstance(epsg, int):
        return epsg
    for k in asset_keys:
        asset = item.assets.get(k)
        if not asset:
            continue
        val = asset.extra_fields.get("proj:epsg")
        if isinstance(val, int):
            return val
    return None


def _no_satellite_item(aoi_id: str, day: str) -> dict:
    return {
        "aoi_id": aoi_id,
        "date": day,
        "status": "no_satellite_item",
        "mean_ndvi": None,
    }


def _refs_key(ingest_prefix: str, day: str, aoi_id: str) -> str:
    return f"{ingest_prefix.rstrip('/')}/aoi_id={aoi_id}/date={day}/s2_refs.json"


def _serialize_aoi_work(aoi_id: str, geometry) -> dict:
    return {
        "aoi_id": aoi_id,
        "geom": geometry.__geo_interface__,
    }


def _compute_ndvi_from_stac(
    geometry,
    stac_url: str,
    collection: str,
    item_id: str,
    b04_asset: str,
    b08_asset: str,
    bbox: list[float],
) -> tuple[float | None, dict | None]:
    # Fetch STAC item, stack assets, and compute mean NDVI for the field.
    for attempt in range(2):
        try:
            catalog = Client.open(stac_url, modifier=pc.sign_inplace)
            stac_item = catalog.get_collection(collection).get_item(item_id)
            epsg = pick_epsg(stac_item, [b04_asset, b08_asset])
            if epsg is None:
                return None, {"status": "missing_crs"}

            data_stack = stackstac.stack(
                [stac_item],
                assets=[b04_asset, b08_asset],
                bounds_latlon=bbox,
                epsg=epsg,
                xy_coords="topleft",
                rescale=True,
                fill_value=np.nan,
                chunksize=512,
                errors_as_nodata=(),
            )

            if data_stack.y.values[0] < data_stack.y.values[-1]:
                data_stack = data_stack.sortby("y", ascending=False)

            # Mask NDVI to the AOI polygon.
            mask = rasterize_geom_mask(data_stack, geometry)
            red_band = data_stack.sel(band=b04_asset).squeeze("time", drop=True)
            nir_band = data_stack.sel(band=b08_asset).squeeze("time", drop=True)

            # Calculate NDVI
            denominator = nir_band + red_band
            ndvi = xr.where(
                denominator != 0, (nir_band - red_band) / denominator, np.nan
            )

            ndvi = ndvi.where(mask)

            mean = ndvi.mean(dim=("y", "x"), skipna=True).compute()
            if np.isfinite(mean.values):
                return float(mean.values), None
            return None, None

        except RasterioIOError:
            if attempt == 0:
                continue
            raise
    return None, None


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
        return ctx["dag_run"].conf or {}

    @task
    def build_aoi_work(conf: dict, day: str) -> list[dict]:
        day = conf.get("date", day)
        fields_gdf = read_gdf_from_s3(conf["fields_with_aoi_s3"])

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

        processed_bucket = conf["processed_bucket"]
        ingest_prefix = conf["ingest_out_prefix"]
        calc_prefix = conf["calc_out_prefix"]

        work = []
        for aoi_id, group in eligible.groupby("aoi_id"):
            out_key = (
                f"{calc_prefix.rstrip('/')}/aoi_timeseries/"
                f"date={day}/aoi_id={aoi_id}/ndvi.json"
            )
            if s3_object_exists(processed_bucket, out_key):
                continue
            refs_key = _refs_key(ingest_prefix, day, aoi_id)
            if not s3_object_exists(processed_bucket, refs_key):
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
        processed_bucket = conf["processed_bucket"]
        ingest_prefix = conf["ingest_out_prefix"]
        day = conf.get("date", day)

        aoi_id = item["aoi_id"]

        refs_key = _refs_key(ingest_prefix, day, aoi_id)
        try:
            refs_obj = get_s3_object(bucket=processed_bucket, key=refs_key)
            refs = json.loads(refs_obj)
        except Exception:
            return _no_satellite_item(aoi_id, day)

        if refs.get("status") != "ok":
            return _no_satellite_item(aoi_id, day)

        aoi_geometry = shape(item["geom"])
        stac_url = refs.get(
            "stac_url", "https://planetarycomputer.microsoft.com/api/stac/v1"
        )
        collection = refs["collection"]
        item_id = refs["item_id"]
        b04_asset = refs["b04_asset"]
        b08_asset = refs["b08_asset"]
        bbox = list(aoi_geometry.bounds)

        mean_ndvi, err = _compute_ndvi_from_stac(
            aoi_geometry,
            stac_url,
            collection,
            item_id,
            b04_asset,
            b08_asset,
            bbox,
        )
        if err is not None and err.get("status") == "missing_crs":
            return {
                "aoi_id": aoi_id,
                "date": day,
                "status": "missing_crs",
                "mean_ndvi": None,
            }

        return {
            "aoi_id": aoi_id,
            "date": day,
            "status": "ok",
            "mean_ndvi": mean_ndvi,
            "cloud_cover": refs.get("cloud_cover"),
            "item_datetime": refs.get("item_datetime"),
        }

    @task
    def write_daily_outputs(results, conf: dict, day: str) -> str:

        processed_bucket = conf["processed_bucket"]
        calc_prefix = conf["calc_out_prefix"]
        day = conf.get("date", day)

        results = list(results)

        aoi_base = f"{calc_prefix.rstrip('/')}/aoi_timeseries/date={day}/"
        for r in results:
            aoi_key = f"{aoi_base}aoi_id={r['aoi_id']}/ndvi.json"
            write_to_s3(
                bucket=processed_bucket,
                key=aoi_key,
                data=json.dumps(r).encode("utf-8"),
                content_type="application/json",
            )

        if results:
            return f"s3://{processed_bucket}/{aoi_base}aoi_id={results[0]['aoi_id']}/ndvi.json"
        return ""

    conf = get_conf()
    day = "{{ ds }}"
    work = build_aoi_work(conf, day)
    results = compute_aoi_ndvi.partial(conf=conf, day=day).expand(item=work)
    write_daily_outputs(results, conf, day)


calculate_daily_ndvi()
