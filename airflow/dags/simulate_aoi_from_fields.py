from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime


import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import box, mapping
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from airflow.sdk import dag, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from plugins.s3_utils import s3_local, download_s3_to_file


def infer_aois_and_tag_fields(
    fields_path: str,
    min_cluster_size: int = 2,
    eps_quantile: float = 0.90,
    padding_m: float = 2000.0,
):
    gdf = gpd.read_file(fields_path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    gdf_m = gdf.to_crs("EPSG:3035")
    cent = gdf_m.geometry.centroid
    X = np.column_stack([cent.x.values, cent.y.values])

    if len(gdf_m) == 1:
        labels = np.array([0], dtype=int)
        eps_used = None
    else:
        nn = NearestNeighbors(n_neighbors=min(2, len(gdf_m))).fit(X)
        dists, _ = nn.kneighbors(X)
        nn_dist = dists[:, 1] if dists.shape[1] > 1 else dists[:, 0]
        eps = float(np.quantile(nn_dist, eps_quantile))
        eps = max(eps, 1000.0)
        eps_used = eps
        labels = DBSCAN(eps=eps, min_samples=min_cluster_size).fit_predict(X)

    gdf_m["cluster"] = labels
    clusters = sorted([c for c in set(labels) if c != -1])
    if not clusters:
        gdf_m["cluster"] = 0
        clusters = [0]

    next_id = max(clusters) + 1
    for idx in gdf_m.index[gdf_m["cluster"] == -1].tolist():
        gdf_m.loc[idx, "cluster"] = next_id
        next_id += 1

    clusters = sorted(set(gdf_m["cluster"].tolist()))
    cluster_to_aoi = {c: f"AOI_{i+1:02d}" for i, c in enumerate(clusters)}

    aois = []
    aoi_features = []

    for c in clusters:
        aoi_id = cluster_to_aoi[c]
        sub = gdf_m[gdf_m["cluster"] == c]
        minx, miny, maxx, maxy = sub.total_bounds
        minx -= padding_m
        miny -= padding_m
        maxx += padding_m
        maxy += padding_m

        aoi_poly_m = box(minx, miny, maxx, maxy)
        aoi_poly_4326 = (
            gpd.GeoDataFrame(
                {"aoi_id": [aoi_id]}, geometry=[aoi_poly_m], crs="EPSG:3035"
            )
            .to_crs("EPSG:4326")
            .geometry.iloc[0]
        )
        minlon, minlat, maxlon, maxlat = aoi_poly_4326.bounds
        bbox = [float(minlon), float(minlat), float(maxlon), float(maxlat)]

        aois.append({"aoi_id": aoi_id, "bbox": bbox})
        aoi_features.append(
            {
                "type": "Feature",
                "properties": {"aoi_id": aoi_id, "bbox": bbox},
                "geometry": mapping(aoi_poly_4326),
            }
        )

    gdf_out = gdf_m.to_crs("EPSG:4326").copy()
    gdf_out["aoi_id"] = gdf_out["cluster"].map(cluster_to_aoi)
    gdf_out = gdf_out.drop(columns=["cluster"])

    aois_geojson = {
        "type": "FeatureCollection",
        "features": aoi_features,
        "properties": {"eps_used_m": eps_used},
    }
    return aois, aois_geojson, gdf_out


@dag(
    dag_id="simulate_aoi_from_fields",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["aoi", "fields", "simulation"],
)
def simulate_aoi_from_fields():
    @task
    def build_and_upload() -> dict:
        raw_bucket = os.environ["RAW_SATELLITE_BUCKET"]
        fields_key = os.environ.get("FIELDS_KEY", "fields/fields.geojson")

        processed_bucket = os.environ["PROCESSED_AOI_BUCKET"]
        out_prefix = os.environ.get("AOI_OUT_PREFIX", "derived/aoi/").rstrip("/") + "/"

        tmpdir = tempfile.mkdtemp(prefix="aoi_")
        fields_path = os.path.join(tmpdir, "fields.geojson")
        download_s3_to_file(raw_bucket, fields_key, fields_path)

        aois, aois_geojson, fields_with_aoi = infer_aois_and_tag_fields(
            fields_path,
            min_cluster_size=int(os.environ.get("AOI_MIN_CLUSTER_SIZE", "2")),
            eps_quantile=float(os.environ.get("AOI_EPS_QUANTILE", "0.90")),
            padding_m=float(os.environ.get("AOI_PADDING_M", "2000")),
        )

        s3 = s3_local()
        aois_json_key = f"{out_prefix}aois.json"
        aois_geojson_key = f"{out_prefix}aois.geojson"
        fields_with_aoi_key = f"{out_prefix}fields_with_aoi.geojson"

        s3.put_object(
            Bucket=processed_bucket,
            Key=aois_json_key,
            Body=json.dumps(aois, indent=2).encode(),
            ContentType="application/json",
        )
        s3.put_object(
            Bucket=processed_bucket,
            Key=aois_geojson_key,
            Body=json.dumps(aois_geojson, indent=2).encode(),
            ContentType="application/geo+json",
        )
        for col in fields_with_aoi.columns:
            if pd.api.types.is_datetime64_any_dtype(fields_with_aoi[col]):
                fields_with_aoi[col] = fields_with_aoi[col].dt.strftime("%Y-%m-%dT%H:%M:%S")

        s3.put_object(
            Bucket=processed_bucket,
            Key=fields_with_aoi_key,
            Body=fields_with_aoi.to_json().encode(),
            ContentType="application/geo+json",
        )

        return {
            "processed_bucket": processed_bucket,
            "aoi_out_prefix": out_prefix,
            "aois_json_s3": f"s3://{processed_bucket}/{aois_json_key}",
            "fields_with_aoi_s3": f"s3://{processed_bucket}/{fields_with_aoi_key}",
            "aois_count": len(aois),
        }

    payload = build_and_upload()

    TriggerDagRunOperator(
        task_id="trigger_ingest_sentinel2_data",
        trigger_dag_id="ingest_sentinel2_data",
        conf=payload,
        wait_for_completion=False,
        reset_dag_run=True,
    )


simulate_aoi_from_fields()
