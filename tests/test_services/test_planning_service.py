# ruff: noqa: E402

import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from services.planning_service import plan_missing_ingest_days


@dataclass
class _Aoi:
    aoi_id: str


def test_plan_missing_ingest_days_returns_empty_for_empty_or_nat_planting_dates():
    aois = [_Aoi("AOI_01")]

    no_rows = pd.DataFrame({"planting_date": []})
    all_nat = pd.DataFrame({"planting_date": [pd.NaT, None]})

    assert (
        plan_missing_ingest_days(
            fields_with_aoi=no_rows,
            aois=aois,
            processed_bucket="processed",
            ingest_prefix="ingest",
            end_day=date(2025, 1, 3),
            exists_fn=lambda *_: False,
        )
        == []
    )
    assert (
        plan_missing_ingest_days(
            fields_with_aoi=all_nat,
            aois=aois,
            processed_bucket="processed",
            ingest_prefix="ingest",
            end_day=date(2025, 1, 3),
            exists_fn=lambda *_: False,
        )
        == []
    )


def test_plan_missing_ingest_days_returns_empty_when_all_refs_exist():
    fields = pd.DataFrame({"planting_date": ["2025-01-01"]})
    aois = [_Aoi("AOI_01"), _Aoi("AOI_02")]

    days = plan_missing_ingest_days(
        fields_with_aoi=fields,
        aois=aois,
        processed_bucket="processed",
        ingest_prefix="ingest",
        end_day=date(2025, 1, 3),
        exists_fn=lambda *_: True,
    )

    assert days == []


def test_plan_missing_ingest_days_returns_partial_missing_days_in_order():
    fields = pd.DataFrame({"planting_date": ["2025-01-01"]})
    aois = [_Aoi("AOI_01"), _Aoi("AOI_02")]

    missing = {
        ("AOI_02", "2025-01-02"),
        ("AOI_01", "2025-01-04"),
    }

    def _exists(_bucket: str, _prefix: str, aoi_id: str, day_str: str) -> bool:
        return (aoi_id, day_str) not in missing

    days = plan_missing_ingest_days(
        fields_with_aoi=fields,
        aois=aois,
        processed_bucket="processed",
        ingest_prefix="ingest",
        end_day=date(2025, 1, 4),
        exists_fn=_exists,
    )

    assert days == ["2025-01-02", "2025-01-04"]
