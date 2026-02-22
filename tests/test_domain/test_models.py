# ruff: noqa: E402

import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from domain.models import (
    Aoi,
    AoiWorkItem,
    IngestRef,
    NdviResult,
    PipelineConf,
)


def test_pipeline_conf_to_from_dict_round_trip():
    model = PipelineConf(
        processed_bucket="processed-aoi",
        derived_out_prefix="derived/",
        ingest_out_prefix="ingest/",
        calc_out_prefix="calculation/",
        aois_json_s3="s3://processed-aoi/derived/aois.json",
        fields_with_aoi_s3="s3://processed-aoi/derived/fields_with_aoi.geojson",
    )

    encoded = model.to_dict()
    decoded = PipelineConf.from_dict(encoded)

    assert decoded == model


def test_aoi_to_from_dict_round_trip():
    model = Aoi(aoi_id="AOI_01", bbox=[10.1, 20.2, 30.3, 40.4])

    encoded = model.to_dict()
    decoded = Aoi.from_dict(encoded)

    assert decoded == model


def test_ingest_ref_to_from_dict_round_trip():
    model = IngestRef(
        aoi_id="AOI_01",
        date="2025-12-01",
        status="ok",
        bbox=[10.1, 20.2, 30.3, 40.4],
        stac_url="https://planetarycomputer.microsoft.com/api/stac/v1",
        collection="sentinel-2-l2a",
        item_id="S2_ITEM_001",
        b04_asset="B04",
        b08_asset="B08",
        cloud_cover=12.5,
        item_datetime="2025-12-01T10:00:00Z",
    )

    encoded = model.to_dict()
    decoded = IngestRef.from_dict(encoded)

    assert decoded == model


def test_ingest_ref_to_from_dict_round_trip_with_optionals_none():
    model = IngestRef(
        aoi_id="AOI_02",
        date="2025-12-02",
        status="no_items",
        bbox=[1.0, 2.0, 3.0, 4.0],
        stac_url=None,
        collection=None,
        item_id=None,
        b04_asset=None,
        b08_asset=None,
        cloud_cover=None,
        item_datetime=None,
    )

    encoded = model.to_dict()
    decoded = IngestRef.from_dict(encoded)

    assert decoded == model


def test_ndvi_result_to_from_dict_round_trip():
    model = NdviResult(
        aoi_id="AOI_01",
        date="2025-12-01",
        status="ok",
        mean_ndvi=0.66,
        cloud_cover=12.5,
        item_datetime="2025-12-01T10:00:00Z",
    )

    encoded = model.to_dict()
    decoded = NdviResult.from_dict(encoded)

    assert decoded == model


def test_ndvi_result_to_from_dict_round_trip_with_optionals_none():
    model = NdviResult(
        aoi_id="AOI_02",
        date="2025-12-02",
        status="no_satellite_item",
        mean_ndvi=None,
        cloud_cover=None,
        item_datetime=None,
    )

    encoded = model.to_dict()
    decoded = NdviResult.from_dict(encoded)

    assert decoded == model


def test_aoi_work_item_to_from_dict_round_trip():
    model = AoiWorkItem(
        aoi_id="AOI_01",
        geom={
            "type": "Polygon",
            "coordinates": [
                [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]
            ],
        },
    )

    encoded = model.to_dict()
    decoded = AoiWorkItem.from_dict(encoded)

    assert decoded == model
