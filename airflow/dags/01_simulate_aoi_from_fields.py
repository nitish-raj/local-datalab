from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime


import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import box
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from airflow.sdk import dag, task
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator
from utils.s3_utils import download_s3_to_file, write_to_s3


def infer_aois_and_tag_fields(
    fields_path: str,
    min_cluster_size: int = 2,
    eps_quantile: float = 0.90,
    padding_m: float = 2000.0,
):
    fields_gdf = gpd.read_file(fields_path)
    if fields_gdf.crs is None:
        fields_gdf = fields_gdf.set_crs("EPSG:4326")
    else:
        fields_gdf = fields_gdf.to_crs("EPSG:4326")

    # Project to meters (LAEA Europe) for clustering distances
    fields_gdf_m = fields_gdf.to_crs("EPSG:3035")

    centroids = fields_gdf_m.geometry.centroid  # Compute centroids for clustering

    centroid_coords = np.column_stack([centroids.x.values, centroids.y.values])

    if len(fields_gdf_m) == 1:
        labels = np.array([0], dtype=int)
    else:
        # Fit NN for eps heuristic
        nn = NearestNeighbors(n_neighbors=min(2, len(fields_gdf_m))).fit(
            centroid_coords
        )
        dists, _ = nn.kneighbors(centroid_coords)
        # Use 2nd neighbor if present
        nn_dist = dists[:, 1] if dists.shape[1] > 1 else dists[:, 0]
        eps = float(np.quantile(nn_dist, eps_quantile))
        eps = max(eps, 1000.0)
        # Cluster centroids
        labels = DBSCAN(eps=eps, min_samples=min_cluster_size).fit_predict(
            centroid_coords
        )

    fields_gdf_m["cluster"] = labels  # Attach cluster labels to rows
    clusters = sorted([c for c in set(labels) if c != -1])
    if not clusters:
        fields_gdf_m["cluster"] = 0
        clusters = [0]

    next_id = max(clusters) + 1
    for idx in fields_gdf_m.index[fields_gdf_m["cluster"] == -1].tolist():
        fields_gdf_m.loc[idx, "cluster"] = next_id
        next_id += 1

    clusters = sorted(set(fields_gdf_m["cluster"].tolist()))  # Final cluster ids
    # Map clusters to AOI ids
    cluster_to_aoi = {c: f"AOI_{i+1:02d}" for i, c in enumerate(clusters)}

    aois = []
    for c in clusters:
        aoi_id = cluster_to_aoi[c]  # Assign AOI id for cluster
        cluster_subset = fields_gdf_m[fields_gdf_m["cluster"] == c]
        minx, miny, maxx, maxy = cluster_subset.total_bounds
        minx -= padding_m
        miny -= padding_m
        maxx += padding_m
        maxy += padding_m

        # Create AOI bbox polygon in meters
        aoi_bbox_m = box(minx, miny, maxx, maxy)
        # Reproject AOI polygon back to EPSG:4326
        aoi_poly_4326 = (
            gpd.GeoDataFrame(
                {"aoi_id": [aoi_id]}, geometry=[aoi_bbox_m], crs="EPSG:3035"
            )
            .to_crs("EPSG:4326")
            .geometry.iloc[0]
        )

        # Extract EPSG:4326 bounds
        minlon, minlat, maxlon, maxlat = aoi_poly_4326.bounds

        # Build bbox list
        bbox = [
            float(minlon),
            float(minlat),
            float(maxlon),
            float(maxlat),
        ]

        aois.append({"aoi_id": aoi_id, "bbox": bbox})

    # Add AOI ids to GeoDataFrame
    fields_out = fields_gdf_m.to_crs("EPSG:4326").copy()
    fields_out["aoi_id"] = fields_out["cluster"].map(cluster_to_aoi)
    fields_out = fields_out.drop(columns=["cluster"])

    return aois, fields_out


@dag(
    dag_id="01_simulate_aoi_from_fields",
    schedule=None,
    start_date=datetime(2025, 12, 1),
    catchup=False,
    default_args={"retries": 3},
    tags=["aoi", "fields", "simulation"],
)
def simulate_aoi_from_fields():
    @task
    def build_and_upload() -> dict:
        raw_bucket = os.environ["RAW_SATELLITE_BUCKET"]
        fields_key = "fields.geojson"

        processed_bucket = os.environ["PROCESSED_AOI_BUCKET"]
        derived_prefix = "derived/".rstrip("/") + "/"
        ingest_prefix = "ingest/".rstrip("/") + "/"
        calc_prefix = "calculation/".rstrip("/") + "/"

        tmpdir = tempfile.mkdtemp(prefix="aoi_")
        fields_path = os.path.join(tmpdir, "fields.geojson")
        download_s3_to_file(raw_bucket, fields_key, fields_path)

        aois, fields_with_aoi = infer_aois_and_tag_fields(
            fields_path,
            min_cluster_size=2,
            eps_quantile=0.90,
            padding_m=2000,
        )

        aois_json_key = f"{derived_prefix}aois.json"
        fields_with_aoi_key = f"{derived_prefix}fields_with_aoi.geojson"

        write_to_s3(
            processed_bucket,
            aois_json_key,
            json.dumps(aois, indent=2).encode(),
            "application/json",
        )

        for col in fields_with_aoi.columns:
            if pd.api.types.is_datetime64_any_dtype(fields_with_aoi[col]):
                fields_with_aoi[col] = fields_with_aoi[col].dt.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )

        write_to_s3(
            processed_bucket,
            fields_with_aoi_key,
            fields_with_aoi.to_json().encode(),
            "application/geo+json",
        )

        return {
            "processed_bucket": processed_bucket,
            "derived_out_prefix": derived_prefix,
            "ingest_out_prefix": ingest_prefix,
            "calc_out_prefix": calc_prefix,
            "aois_json_s3": f"s3://{processed_bucket}/{aois_json_key}",
            "fields_with_aoi_s3": f"s3://{processed_bucket}/{fields_with_aoi_key}",
            "aois_count": len(aois),
        }

    payload = build_and_upload()

    TriggerDagRunOperator(
        task_id="trigger_ingest_sentinel2_data",
        trigger_dag_id="02_ingest_sentinel2_data",
        conf=payload,
        wait_for_completion=False,
        reset_dag_run=True,
    )


simulate_aoi_from_fields()
