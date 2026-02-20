from __future__ import annotations

import numpy as np
import planetary_computer as pc
from pystac_client import Client
from rasterio.errors import RasterioIOError
from rasterio.features import rasterize
from rasterio.transform import from_origin
import stackstac
import xarray as xr

from domain.models import IngestRef, NdviResult


DEFAULT_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def pick_epsg(item, asset_keys: list[str]) -> int | None:
    epsg = item.properties.get("proj:epsg")
    if isinstance(epsg, int):
        return epsg

    for asset_key in asset_keys:
        asset = item.assets.get(asset_key)
        if not asset:
            continue
        asset_epsg = asset.extra_fields.get("proj:epsg")
        if isinstance(asset_epsg, int):
            return asset_epsg

    return None


def rasterize_geom_mask(data_stack: xr.DataArray, geom4326) -> xr.DataArray:
    x_coords = data_stack.x.values
    y_coords = data_stack.y.values
    if x_coords.size < 2 or y_coords.size < 2:
        mask = np.ones((y_coords.size, x_coords.size), dtype=bool)
        return xr.DataArray(
            mask,
            coords={"y": data_stack.y, "x": data_stack.x},
            dims=("y", "x"),
        )

    x_res = float(x_coords[1] - x_coords[0])
    y_res = float(y_coords[0] - y_coords[1])
    transform = from_origin(
        float(x_coords[0]),
        float(y_coords[0]),
        abs(x_res),
        abs(y_res),
    )

    mask = rasterize(
        [geom4326],
        out_shape=(y_coords.size, x_coords.size),
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
    ).astype(bool)
    return xr.DataArray(
        mask, coords={"y": data_stack.y, "x": data_stack.x}, dims=("y", "x")
    )


def compute_ndvi_for_aoi(geometry, ref: IngestRef) -> NdviResult:
    if ref.status != "ok":
        return NdviResult(
            aoi_id=ref.aoi_id,
            date=ref.date,
            status="no_satellite_item",
            mean_ndvi=None,
            cloud_cover=None,
            item_datetime=None,
        )

    asset_keys = [ref.b04_asset, ref.b08_asset]

    for attempt in range(2):
        try:
            catalog = Client.open(
                ref.stac_url or DEFAULT_STAC_URL, modifier=pc.sign_inplace
            )
            stac_item = catalog.get_collection(ref.collection).get_item(ref.item_id)

            epsg = pick_epsg(stac_item, asset_keys)
            if epsg is None:
                return NdviResult(
                    aoi_id=ref.aoi_id,
                    date=ref.date,
                    status="missing_crs",
                    mean_ndvi=None,
                    cloud_cover=ref.cloud_cover,
                    item_datetime=ref.item_datetime,
                )

            data_stack = stackstac.stack(
                [stac_item],
                assets=asset_keys,
                bounds_latlon=list(geometry.bounds),
                epsg=epsg,
                xy_coords="topleft",
                rescale=True,
                fill_value=np.nan,
                chunksize=512,
                errors_as_nodata=(),
            )

            if data_stack.y.values[0] < data_stack.y.values[-1]:
                data_stack = data_stack.sortby("y", ascending=False)

            mask = rasterize_geom_mask(data_stack, geometry)
            red_band = data_stack.sel(band=ref.b04_asset).squeeze("time", drop=True)
            nir_band = data_stack.sel(band=ref.b08_asset).squeeze("time", drop=True)

            denominator = nir_band + red_band
            ndvi = xr.where(
                denominator != 0, (nir_band - red_band) / denominator, np.nan
            )
            ndvi = ndvi.where(mask)

            mean = ndvi.mean(dim=("y", "x"), skipna=True).compute()
            mean_ndvi = float(mean.values) if np.isfinite(mean.values) else None

            return NdviResult(
                aoi_id=ref.aoi_id,
                date=ref.date,
                status="ok",
                mean_ndvi=mean_ndvi,
                cloud_cover=ref.cloud_cover,
                item_datetime=ref.item_datetime,
            )

        except RasterioIOError:
            if attempt == 0:
                continue
            raise

    return NdviResult(
        aoi_id=ref.aoi_id,
        date=ref.date,
        status="ok",
        mean_ndvi=None,
        cloud_cover=ref.cloud_cover,
        item_datetime=ref.item_datetime,
    )
