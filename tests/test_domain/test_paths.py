# ruff: noqa: E402

import sys
from pathlib import Path

import pytest


REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from domain.paths import (
    aois_key,
    fields_with_aoi_key,
    ingest_ref_key,
    ndvi_day_prefix,
    ndvi_key,
)


@pytest.mark.parametrize("derived_prefix", ["derived", "derived/"])
def test_aois_key_exact_output(derived_prefix: str):
    assert aois_key(derived_prefix) == "derived/aois.json"


@pytest.mark.parametrize("derived_prefix", ["derived", "derived/"])
def test_fields_with_aoi_key_exact_output(derived_prefix: str):
    assert fields_with_aoi_key(derived_prefix) == "derived/fields_with_aoi.geojson"


@pytest.mark.parametrize("ingest_prefix", ["ingest", "ingest/"])
def test_ingest_ref_key_exact_output(ingest_prefix: str):
    assert (
        ingest_ref_key(ingest_prefix, "AOI_01", "2025-12-01")
        == "ingest/aoi_id=AOI_01/date=2025-12-01/s2_refs.json"
    )


@pytest.mark.parametrize("calc_prefix", ["calculation", "calculation/"])
def test_ndvi_key_exact_output(calc_prefix: str):
    assert (
        ndvi_key(calc_prefix, "AOI_01", "2025-12-01")
        == "calculation/aoi_timeseries/date=2025-12-01/aoi_id=AOI_01/ndvi.json"
    )


@pytest.mark.parametrize("calc_prefix", ["calculation", "calculation/"])
def test_ndvi_day_prefix_exact_output(calc_prefix: str):
    assert (
        ndvi_day_prefix(calc_prefix, "2025-12-01")
        == "calculation/aoi_timeseries/date=2025-12-01/"
    )
