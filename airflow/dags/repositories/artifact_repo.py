from __future__ import annotations

import json

import geopandas as gpd

from domain.models import Aoi, IngestRef, NdviResult
from domain.paths import ingest_ref_key, ndvi_key
from utils.s3_utils import (
    get_s3_object,
    parse_s3,
    read_gdf_from_s3,
    s3_object_exists,
    write_to_s3,
)


def _json_text(raw: str | bytes) -> str:
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    if isinstance(raw, str):
        return raw
    raise TypeError(f"Expected S3 object body as str or bytes, got {type(raw)!r}")


def read_aois(s3_uri: str) -> list[Aoi]:
    bucket, key = parse_s3(s3_uri)
    payload = json.loads(_json_text(get_s3_object(bucket=bucket, key=key)))
    return [Aoi.from_dict(item) for item in payload]


def write_aois(bucket: str, key: str, aois: list[Aoi]) -> None:
    payload = [aoi.to_dict() for aoi in aois]
    write_to_s3(
        bucket=bucket,
        key=key,
        data=json.dumps(payload).encode("utf-8"),
        content_type="application/json",
    )


def read_fields_with_aoi(s3_uri: str) -> gpd.GeoDataFrame:
    return read_gdf_from_s3(s3_uri)


def write_fields_with_aoi(bucket: str, key: str, fields_gdf: gpd.GeoDataFrame) -> None:
    write_to_s3(
        bucket=bucket,
        key=key,
        data=fields_gdf.to_json().encode("utf-8"),
        content_type="application/geo+json",
    )


def ingest_ref_exists(bucket: str, ingest_prefix: str, aoi_id: str, day: str) -> bool:
    key = ingest_ref_key(ingest_prefix, aoi_id, day)
    return s3_object_exists(bucket=bucket, key=key)


def read_ingest_ref(
    bucket: str, ingest_prefix: str, aoi_id: str, day: str
) -> IngestRef:
    key = ingest_ref_key(ingest_prefix, aoi_id, day)
    payload = json.loads(_json_text(get_s3_object(bucket=bucket, key=key)))
    return IngestRef.from_dict(payload)


def write_ingest_ref(bucket: str, ingest_prefix: str, ref: IngestRef) -> None:
    key = ingest_ref_key(ingest_prefix, ref.aoi_id, ref.date)
    write_to_s3(
        bucket=bucket,
        key=key,
        data=json.dumps(ref.to_dict()).encode("utf-8"),
        content_type="application/json",
    )


def ndvi_exists(bucket: str, calc_prefix: str, aoi_id: str, day: str) -> bool:
    key = ndvi_key(calc_prefix, aoi_id, day)
    return s3_object_exists(bucket=bucket, key=key)


def ndvi_payload(result: NdviResult) -> dict:
    payload = {
        "aoi_id": result.aoi_id,
        "date": result.date,
        "status": result.status,
        "mean_ndvi": result.mean_ndvi,
    }
    if result.status == "ok":
        payload["cloud_cover"] = result.cloud_cover
        payload["item_datetime"] = result.item_datetime
    return payload


def write_ndvi_result(bucket: str, calc_prefix: str, result: NdviResult) -> None:
    key = ndvi_key(calc_prefix, result.aoi_id, result.date)
    write_to_s3(
        bucket=bucket,
        key=key,
        data=json.dumps(ndvi_payload(result)).encode("utf-8"),
        content_type="application/json",
    )
