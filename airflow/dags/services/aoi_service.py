from __future__ import annotations

import numpy as np
from geopandas import GeoDataFrame
from shapely.geometry import box

from domain.models import Aoi


def infer_aois_and_tag_fields(
    fields_gdf: GeoDataFrame,
    min_cluster_size: int,
    eps_quantile: float,
    padding_m: float,
) -> tuple[list[Aoi], GeoDataFrame]:
    from sklearn.cluster import DBSCAN
    from sklearn.neighbors import NearestNeighbors

    if fields_gdf.crs is None:
        fields_gdf = fields_gdf.set_crs("EPSG:4326")
    else:
        fields_gdf = fields_gdf.to_crs("EPSG:4326")

    fields_gdf_m = fields_gdf.to_crs("EPSG:3035")
    centroids = fields_gdf_m.geometry.centroid
    centroid_coords = np.column_stack([centroids.x.values, centroids.y.values])

    if len(fields_gdf_m) == 1:
        labels = np.array([0], dtype=int)
    else:
        nn = NearestNeighbors(n_neighbors=min(2, len(fields_gdf_m))).fit(
            centroid_coords
        )
        dists, _ = nn.kneighbors(centroid_coords)
        nn_dist = dists[:, 1] if dists.shape[1] > 1 else dists[:, 0]
        eps = float(np.quantile(nn_dist, eps_quantile))
        eps = max(eps, 1000.0)
        labels = DBSCAN(eps=eps, min_samples=min_cluster_size).fit_predict(
            centroid_coords
        )

    fields_gdf_m["cluster"] = labels
    clusters = sorted([c for c in set(labels) if c != -1])
    if not clusters:
        fields_gdf_m["cluster"] = 0
        clusters = [0]

    next_id = max(clusters) + 1
    for idx in fields_gdf_m.index[fields_gdf_m["cluster"] == -1].tolist():
        fields_gdf_m.loc[idx, "cluster"] = next_id
        next_id += 1

    clusters = sorted(set(fields_gdf_m["cluster"].tolist()))
    cluster_to_aoi = {c: f"AOI_{i + 1:02d}" for i, c in enumerate(clusters)}

    aois = []
    for cluster_id in clusters:
        aoi_id = cluster_to_aoi[cluster_id]
        cluster_subset = fields_gdf_m[fields_gdf_m["cluster"] == cluster_id]
        minx, miny, maxx, maxy = cluster_subset.total_bounds
        minx -= padding_m
        miny -= padding_m
        maxx += padding_m
        maxy += padding_m

        aoi_bbox_m = box(minx, miny, maxx, maxy)
        aoi_poly_4326 = (
            GeoDataFrame({"aoi_id": [aoi_id]}, geometry=[aoi_bbox_m], crs="EPSG:3035")
            .to_crs("EPSG:4326")
            .geometry.iloc[0]
        )

        minlon, minlat, maxlon, maxlat = aoi_poly_4326.bounds
        aois.append(
            Aoi(
                aoi_id=aoi_id,
                bbox=[
                    float(minlon),
                    float(minlat),
                    float(maxlon),
                    float(maxlat),
                ],
            )
        )

    fields_out = fields_gdf_m.to_crs("EPSG:4326").copy()
    fields_out["aoi_id"] = fields_out["cluster"].map(cluster_to_aoi)
    fields_out = fields_out.drop(columns=["cluster"])

    return aois, fields_out
