from __future__ import annotations


def _normalize_prefix(prefix: str) -> str:
    return prefix.rstrip("/") + "/"


def _normalize_prefix_no_trailing_slash(prefix: str) -> str:
    return prefix.rstrip("/")


def aois_key(derived_prefix: str) -> str:
    return f"{_normalize_prefix(derived_prefix)}aois.json"


def fields_with_aoi_key(derived_prefix: str) -> str:
    return f"{_normalize_prefix(derived_prefix)}fields_with_aoi.geojson"


def ingest_ref_key(ingest_prefix: str, aoi_id: str, day: str) -> str:
    return f"{_normalize_prefix(ingest_prefix)}aoi_id={aoi_id}/date={day}/s2_refs.json"


def ndvi_key(calc_prefix: str, aoi_id: str, day: str) -> str:
    return (
        f"{_normalize_prefix_no_trailing_slash(calc_prefix)}"
        f"/aoi_timeseries/date={day}/aoi_id={aoi_id}/ndvi.json"
    )


def ndvi_day_prefix(calc_prefix: str, day: str) -> str:
    return (
        f"{_normalize_prefix_no_trailing_slash(calc_prefix)}/aoi_timeseries/date={day}/"
    )
