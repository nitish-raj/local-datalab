# ruff: noqa: E402

import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from domain.models import Aoi
from services import stac_service


class _FakeSearch:
    def __init__(self, items):
        self._items = items

    def items(self):
        return self._items


class _FakeCatalog:
    def __init__(self, items, calls):
        self._items = items
        self._calls = calls

    def search(self, **kwargs):
        self._calls.append(kwargs)
        return _FakeSearch(self._items)


class _FakeItem:
    def __init__(self, item_id, assets, cloud_cover, dt):
        self.id = item_id
        self.assets = assets
        self.properties = {
            "eo:cloud_cover": cloud_cover,
            "datetime": dt,
        }


def test_pick_asset_id_prefers_direct_match():
    item = _FakeItem(
        item_id="ITEM_001",
        assets={"B04": object(), "B08": object()},
        cloud_cover=5.0,
        dt="2025-12-01T10:00:00Z",
    )

    assert stac_service.pick_asset_id(item, ["B04", "red"]) == "B04"


def test_pick_asset_id_supports_case_insensitive_match():
    item = _FakeItem(
        item_id="ITEM_001",
        assets={"b08": object()},
        cloud_cover=5.0,
        dt="2025-12-01T10:00:00Z",
    )

    assert stac_service.pick_asset_id(item, ["B08", "nir"]) == "b08"


def test_fetch_ingest_ref_returns_no_items_when_search_empty(monkeypatch):
    search_calls = []
    fake_catalog = _FakeCatalog([], search_calls)

    class _FakeClient:
        @staticmethod
        def open(*args, **kwargs):
            return fake_catalog

    monkeypatch.setattr(stac_service, "Client", _FakeClient)

    ref = stac_service.fetch_ingest_ref(
        aoi=Aoi(aoi_id="AOI_01", bbox=[1.0, 2.0, 3.0, 4.0]),
        day="2025-12-01",
        max_cloud=30.0,
        stac_url="https://example.com/stac",
        collection="sentinel-2-l2a",
    )

    assert ref.status == "no_items"
    assert ref.aoi_id == "AOI_01"
    assert ref.date == "2025-12-01"
    assert ref.bbox == [1.0, 2.0, 3.0, 4.0]
    assert ref.item_id is None
    assert ref.b04_asset is None
    assert ref.b08_asset is None
    assert search_calls == [
        {
            "collections": ["sentinel-2-l2a"],
            "bbox": [1.0, 2.0, 3.0, 4.0],
            "datetime": "2025-12-01T00:00:00Z/2025-12-01T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": 30.0}},
            "max_items": 50,
        }
    ]


def test_fetch_ingest_ref_picks_best_item_and_maps_fields(monkeypatch):
    items = [
        _FakeItem(
            item_id="ITEM_LATE",
            assets={"B04": object(), "B08": object()},
            cloud_cover=5.0,
            dt="2025-12-01T11:00:00Z",
        ),
        _FakeItem(
            item_id="ITEM_BEST",
            assets={"b04": object(), "b08": object()},
            cloud_cover=5.0,
            dt="2025-12-01T09:00:00Z",
        ),
        _FakeItem(
            item_id="ITEM_CLOUDY",
            assets={"B04": object(), "B08": object()},
            cloud_cover=12.0,
            dt="2025-12-01T08:00:00Z",
        ),
    ]
    fake_catalog = _FakeCatalog(items, [])

    class _FakeClient:
        @staticmethod
        def open(*args, **kwargs):
            return fake_catalog

    monkeypatch.setattr(stac_service, "Client", _FakeClient)

    ref = stac_service.fetch_ingest_ref(
        aoi=Aoi(aoi_id="AOI_01", bbox=[1.0, 2.0, 3.0, 4.0]),
        day="2025-12-01",
        max_cloud=30.0,
        stac_url="https://example.com/stac",
        collection="sentinel-2-l2a",
    )

    assert ref.status == "ok"
    assert ref.item_id == "ITEM_BEST"
    assert ref.cloud_cover == 5.0
    assert ref.item_datetime == "2025-12-01T09:00:00Z"
    assert ref.b04_asset == "b04"
    assert ref.b08_asset == "b08"
    assert ref.stac_url == "https://example.com/stac"
    assert ref.collection == "sentinel-2-l2a"
