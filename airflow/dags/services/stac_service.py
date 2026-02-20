from __future__ import annotations

from domain.models import Aoi, IngestRef
import planetary_computer as pc
from pystac_client import Client


def pick_asset_id(item, candidates) -> str:
    keys = list(item.assets.keys())
    for candidate in candidates:
        if candidate in item.assets:
            return candidate
    for candidate in candidates:
        for key in keys:
            if candidate.lower() == key.lower():
                return key
    raise KeyError(f"Missing asset {candidates}. Available: {keys[:80]}")


def fetch_ingest_ref(
    aoi: Aoi,
    day: str,
    max_cloud: float,
    stac_url: str,
    collection: str,
) -> IngestRef:
    dt = f"{day}T00:00:00Z/{day}T23:59:59Z"
    catalog = Client.open(stac_url, modifier=pc.sign_inplace)
    search = catalog.search(
        collections=[collection],
        bbox=aoi.bbox,
        datetime=dt,
        query={"eo:cloud_cover": {"lt": max_cloud}},
        max_items=50,
    )
    items = list(search.items())

    if not items:
        return IngestRef(
            aoi_id=aoi.aoi_id,
            date=day,
            status="no_items",
            bbox=list(aoi.bbox),
            stac_url=None,
            collection=None,
            item_id=None,
            b04_asset=None,
            b08_asset=None,
            cloud_cover=None,
            item_datetime=None,
        )

    items.sort(
        key=lambda item: (
            item.properties.get("eo:cloud_cover", 999.0),
            item.properties.get("datetime", ""),
        )
    )
    item = items[0]

    return IngestRef(
        aoi_id=aoi.aoi_id,
        date=day,
        status="ok",
        bbox=list(aoi.bbox),
        stac_url=stac_url,
        collection=collection,
        item_id=item.id,
        b04_asset=pick_asset_id(item, ["B04", "B04_10m", "red"]),
        b08_asset=pick_asset_id(item, ["B08", "B08_10m", "nir"]),
        cloud_cover=item.properties.get("eo:cloud_cover"),
        item_datetime=item.properties.get("datetime"),
    )
