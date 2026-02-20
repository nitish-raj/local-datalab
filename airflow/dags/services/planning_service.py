from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Protocol

import pandas as pd

from repositories.artifact_repo import ingest_ref_exists


class _AoiLike(Protocol):
    aoi_id: str


def normalize_planting_dates(fields_with_aoi: pd.DataFrame) -> pd.Series:
    if "planting_date" not in fields_with_aoi.columns:
        raise ValueError("fields_with_aoi.geojson must contain 'planting_date'")
    return pd.to_datetime(fields_with_aoi["planting_date"]).dt.date


def compute_start_day(fields_with_aoi: pd.DataFrame) -> date | None:
    planting_dates = normalize_planting_dates(fields_with_aoi)
    start_day = planting_dates.dropna().min()
    if start_day is None or pd.isna(start_day):
        return None
    return start_day


def plan_missing_ingest_days(
    fields_with_aoi: pd.DataFrame,
    aois: Sequence[_AoiLike],
    processed_bucket: str,
    ingest_prefix: str,
    *,
    end_day: date | None = None,
    exists_fn: Callable[[str, str, str, str], bool] = ingest_ref_exists,
) -> list[str]:
    start_day = compute_start_day(fields_with_aoi)
    if start_day is None:
        return []

    if end_day is None:
        end_day = datetime.now(timezone.utc).date()

    days: list[str] = []
    current_day = start_day
    while current_day <= end_day:
        day_str = current_day.isoformat()
        day_missing = False
        for aoi in aois:
            if not exists_fn(processed_bucket, ingest_prefix, aoi.aoi_id, day_str):
                day_missing = True
                break
        if day_missing:
            days.append(day_str)
        current_day += timedelta(days=1)

    return days
