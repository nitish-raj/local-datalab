# ruff: noqa: E402

import sys
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from services.aoi_service import infer_aois_and_tag_fields


def test_infer_aois_and_tag_fields_single_field_creates_one_aoi():
    fields_gdf = gpd.GeoDataFrame(
        {"field_id": ["F1"], "geometry": [Point(12.0, 48.0)]},
        crs="EPSG:4326",
    )

    aois, tagged = infer_aois_and_tag_fields(
        fields_gdf,
        min_cluster_size=2,
        eps_quantile=0.9,
        padding_m=2000,
    )

    assert len(aois) == 1
    assert aois[0].aoi_id == "AOI_01"
    assert len(aois[0].bbox) == 4
    assert tagged["aoi_id"].tolist() == ["AOI_01"]


def test_infer_aois_and_tag_fields_multi_with_noise_assigns_unique_aoi():
    fields_gdf = gpd.GeoDataFrame(
        {
            "field_id": ["F1", "F2", "F3"],
            "geometry": [
                Point(10.0, 50.0),
                Point(10.002, 50.001),
                Point(25.0, 60.0),
            ],
        },
        crs="EPSG:4326",
    )

    aois, tagged = infer_aois_and_tag_fields(
        fields_gdf,
        min_cluster_size=2,
        eps_quantile=0.9,
        padding_m=2000,
    )

    assert len(aois) == 2
    assert tagged.iloc[0]["aoi_id"] == tagged.iloc[1]["aoi_id"]
    assert tagged.iloc[2]["aoi_id"] != tagged.iloc[0]["aoi_id"]
    assert set(tagged["aoi_id"]) == {"AOI_01", "AOI_02"}
