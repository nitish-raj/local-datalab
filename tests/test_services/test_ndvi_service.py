# ruff: noqa: E402

import sys
from pathlib import Path

import numpy as np
import xarray as xr
from shapely.geometry import Point, box

REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from domain.models import IngestRef
from services import ndvi_service


class _FakeAsset:
    def __init__(self, epsg):
        self.extra_fields = {"proj:epsg": epsg}


class _FakeItem:
    def __init__(self, item_epsg=None, asset_epsg=None):
        self.properties = {}
        if item_epsg is not None:
            self.properties["proj:epsg"] = item_epsg
        self.assets = {
            "B04": _FakeAsset(asset_epsg),
            "B08": _FakeAsset(asset_epsg),
        }


def test_pick_epsg_prefers_item_level_epsg():
    item = _FakeItem(item_epsg=32632, asset_epsg=4326)

    epsg = ndvi_service.pick_epsg(item, ["B04", "B08"])

    assert epsg == 32632


def test_pick_epsg_falls_back_to_asset_level_epsg():
    item = _FakeItem(item_epsg=None, asset_epsg=32631)

    epsg = ndvi_service.pick_epsg(item, ["B04", "B08"])

    assert epsg == 32631


def test_rasterize_geom_mask_tiny_stack_returns_expected_shape():
    data = xr.DataArray(
        np.array([[[[1.0]]]], dtype=np.float32),
        dims=("time", "band", "y", "x"),
        coords={
            "time": [0],
            "band": ["B04"],
            "y": [50.0],
            "x": [10.0],
        },
    )

    mask = ndvi_service.rasterize_geom_mask(data, box(9.5, 49.5, 10.5, 50.5))

    assert mask.shape == (1, 1)
    assert bool(mask.values[0, 0]) is True


def test_compute_ndvi_for_aoi_returns_no_satellite_when_ref_not_ok(monkeypatch):
    called = {"value": False}

    class _FakeClient:
        @staticmethod
        def open(*args, **kwargs):
            called["value"] = True
            return None

    monkeypatch.setattr(ndvi_service, "Client", _FakeClient)

    ref = IngestRef(
        aoi_id="AOI_01",
        date="2025-12-01",
        status="no_items",
        bbox=[1.0, 2.0, 3.0, 4.0],
        stac_url="https://example.com/stac",
        collection="sentinel-2-l2a",
        item_id="ITEM_001",
        b04_asset="B04",
        b08_asset="B08",
        cloud_cover=None,
        item_datetime=None,
    )

    result = ndvi_service.compute_ndvi_for_aoi(Point(10.0, 50.0), ref)

    assert result.status == "no_satellite_item"
    assert result.mean_ndvi is None
    assert called["value"] is False


def test_compute_ndvi_for_aoi_returns_missing_crs_when_item_has_no_epsg(monkeypatch):
    fake_item = _FakeItem(item_epsg=None, asset_epsg=None)

    class _FakeCollection:
        def get_item(self, item_id):
            assert item_id == "ITEM_001"
            return fake_item

    class _FakeCatalog:
        def get_collection(self, collection):
            assert collection == "sentinel-2-l2a"
            return _FakeCollection()

    class _FakeClient:
        @staticmethod
        def open(*args, **kwargs):
            return _FakeCatalog()

    monkeypatch.setattr(ndvi_service, "Client", _FakeClient)

    ref = IngestRef(
        aoi_id="AOI_01",
        date="2025-12-01",
        status="ok",
        bbox=[1.0, 2.0, 3.0, 4.0],
        stac_url="https://example.com/stac",
        collection="sentinel-2-l2a",
        item_id="ITEM_001",
        b04_asset="B04",
        b08_asset="B08",
        cloud_cover=5.0,
        item_datetime="2025-12-01T10:00:00Z",
    )

    result = ndvi_service.compute_ndvi_for_aoi(Point(10.0, 50.0), ref)

    assert result.status == "missing_crs"
    assert result.mean_ndvi is None
