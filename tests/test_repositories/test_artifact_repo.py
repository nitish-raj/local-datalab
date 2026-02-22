# ruff: noqa: E402

import json
import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from domain.models import Aoi, IngestRef, NdviResult
from repositories import artifact_repo


def test_read_aois_decodes_json_from_bytes(monkeypatch):
    payload = [{"aoi_id": "AOI_01", "bbox": [1, 2, 3, 4]}]

    monkeypatch.setattr(
        artifact_repo,
        "get_s3_object",
        lambda bucket, key: json.dumps(payload).encode("utf-8"),
    )

    aois = artifact_repo.read_aois("s3://processed/derived/aois.json")

    assert aois == [Aoi(aoi_id="AOI_01", bbox=[1.0, 2.0, 3.0, 4.0])]


def test_write_aois_sets_json_content_type(monkeypatch):
    captured = {}

    def fake_write_to_s3(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(artifact_repo, "write_to_s3", fake_write_to_s3)

    artifact_repo.write_aois(
        bucket="processed",
        key="derived/aois.json",
        aois=[Aoi(aoi_id="AOI_01", bbox=[1.0, 2.0, 3.0, 4.0])],
    )

    assert captured["bucket"] == "processed"
    assert captured["key"] == "derived/aois.json"
    assert captured["content_type"] == "application/json"
    assert json.loads(captured["data"].decode("utf-8")) == [
        {"aoi_id": "AOI_01", "bbox": [1.0, 2.0, 3.0, 4.0]}
    ]


def test_write_fields_with_aoi_sets_geojson_content_type(monkeypatch):
    captured = {}

    def fake_write_to_s3(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(artifact_repo, "write_to_s3", fake_write_to_s3)

    fields_gdf = gpd.GeoDataFrame(
        {"aoi_id": ["AOI_01"], "geometry": [Point(10.0, 20.0)]}, crs="EPSG:4326"
    )

    artifact_repo.write_fields_with_aoi(
        bucket="processed",
        key="derived/fields_with_aoi.geojson",
        fields_gdf=fields_gdf,
    )

    assert captured["bucket"] == "processed"
    assert captured["key"] == "derived/fields_with_aoi.geojson"
    assert captured["content_type"] == "application/geo+json"
    assert json.loads(captured["data"].decode("utf-8"))["type"] == "FeatureCollection"


def test_exists_checks_use_path_builders(monkeypatch):
    calls = []

    def fake_exists(bucket, key):
        calls.append((bucket, key))
        return key.startswith("ingest/")

    monkeypatch.setattr(
        artifact_repo,
        "ingest_ref_key",
        lambda ingest_prefix, aoi_id, day: f"ingest/{aoi_id}/{day}.json",
    )
    monkeypatch.setattr(
        artifact_repo,
        "ndvi_key",
        lambda calc_prefix, aoi_id, day: f"calc/{day}/{aoi_id}.json",
    )
    monkeypatch.setattr(artifact_repo, "s3_object_exists", fake_exists)

    ingest_exists = artifact_repo.ingest_ref_exists(
        "processed", "ingest/", "AOI_01", "2025-12-01"
    )
    ndvi_exists = artifact_repo.ndvi_exists(
        "processed", "calculation/", "AOI_01", "2025-12-01"
    )

    assert ingest_exists is True
    assert ndvi_exists is False
    assert calls == [
        ("processed", "ingest/AOI_01/2025-12-01.json"),
        ("processed", "calc/2025-12-01/AOI_01.json"),
    ]


def test_read_ingest_ref_decodes_json_text_and_bytes(monkeypatch):
    payload = {
        "aoi_id": "AOI_01",
        "date": "2025-12-01",
        "status": "ok",
        "bbox": [1, 2, 3, 4],
        "stac_url": "https://example.com/stac",
        "collection": "sentinel-2-l2a",
        "item_id": "ITEM_001",
        "b04_asset": "B04",
        "b08_asset": "B08",
        "cloud_cover": 12.5,
        "item_datetime": "2025-12-01T10:00:00Z",
    }
    monkeypatch.setattr(
        artifact_repo,
        "ingest_ref_key",
        lambda ingest_prefix, aoi_id, day: "ingest/key.json",
    )

    monkeypatch.setattr(
        artifact_repo,
        "get_s3_object",
        lambda bucket, key: json.dumps(payload).encode("utf-8"),
    )
    decoded_bytes = artifact_repo.read_ingest_ref(
        "processed", "ingest/", "AOI_01", "2025-12-01"
    )

    monkeypatch.setattr(
        artifact_repo,
        "get_s3_object",
        lambda bucket, key: json.dumps(payload),
    )
    decoded_text = artifact_repo.read_ingest_ref(
        "processed", "ingest/", "AOI_01", "2025-12-01"
    )

    expected = IngestRef.from_dict(payload)
    assert decoded_bytes == expected
    assert decoded_text == expected


def test_write_ingest_ref_and_ndvi_result_use_built_keys(monkeypatch):
    writes = []

    def fake_write_to_s3(**kwargs):
        writes.append(kwargs)

    monkeypatch.setattr(artifact_repo, "write_to_s3", fake_write_to_s3)
    monkeypatch.setattr(
        artifact_repo,
        "ingest_ref_key",
        lambda ingest_prefix, aoi_id, day: f"ingest/{aoi_id}/{day}/s2_refs.json",
    )
    monkeypatch.setattr(
        artifact_repo,
        "ndvi_key",
        lambda calc_prefix, aoi_id, day: f"calc/{day}/{aoi_id}/ndvi.json",
    )

    artifact_repo.write_ingest_ref(
        bucket="processed",
        ingest_prefix="ingest/",
        ref=IngestRef(
            aoi_id="AOI_01",
            date="2025-12-01",
            status="ok",
            bbox=[1.0, 2.0, 3.0, 4.0],
            stac_url="https://example.com/stac",
            collection="sentinel-2-l2a",
            item_id="ITEM_001",
            b04_asset="B04",
            b08_asset="B08",
            cloud_cover=12.5,
            item_datetime="2025-12-01T10:00:00Z",
        ),
    )
    artifact_repo.write_ndvi_result(
        bucket="processed",
        calc_prefix="calculation/",
        result=NdviResult(
            aoi_id="AOI_01",
            date="2025-12-01",
            status="ok",
            mean_ndvi=0.66,
            cloud_cover=12.5,
            item_datetime="2025-12-01T10:00:00Z",
        ),
    )

    assert writes[0]["key"] == "ingest/AOI_01/2025-12-01/s2_refs.json"
    assert writes[0]["content_type"] == "application/json"
    assert writes[1]["key"] == "calc/2025-12-01/AOI_01/ndvi.json"
    assert writes[1]["content_type"] == "application/json"
    assert json.loads(writes[1]["data"].decode("utf-8")) == {
        "aoi_id": "AOI_01",
        "date": "2025-12-01",
        "status": "ok",
        "mean_ndvi": 0.66,
        "cloud_cover": 12.5,
        "item_datetime": "2025-12-01T10:00:00Z",
    }


def test_write_ndvi_result_omits_cloud_fields_when_status_not_ok(monkeypatch):
    captured = {}

    def fake_write_to_s3(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(artifact_repo, "write_to_s3", fake_write_to_s3)
    monkeypatch.setattr(
        artifact_repo,
        "ndvi_key",
        lambda calc_prefix, aoi_id, day: f"calc/{day}/{aoi_id}/ndvi.json",
    )

    artifact_repo.write_ndvi_result(
        bucket="processed",
        calc_prefix="calculation/",
        result=NdviResult(
            aoi_id="AOI_01",
            date="2025-12-01",
            status="missing_crs",
            mean_ndvi=None,
            cloud_cover=12.5,
            item_datetime="2025-12-01T10:00:00Z",
        ),
    )

    assert json.loads(captured["data"].decode("utf-8")) == {
        "aoi_id": "AOI_01",
        "date": "2025-12-01",
        "status": "missing_crs",
        "mean_ndvi": None,
    }
