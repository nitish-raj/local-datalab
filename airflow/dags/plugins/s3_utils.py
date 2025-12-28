import boto3
import os
import tempfile
from botocore.config import Config
import geopandas as gpd


def s3_local():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        config=Config(s3={"addressing_style": "path"}),
    )


def download_s3_to_file(bucket: str, key: str, out_path: str):
    s3 = s3_local()
    obj = s3.get_object(Bucket=bucket, Key=key)
    with open(out_path, "wb") as f:
        f.write(obj["Body"].read())


def parse_s3(uri: str):
    b, k = uri[5:].split("/", 1)
    return b, k


def read_gdf_from_s3(uri: str) -> gpd.GeoDataFrame:
    bkt, key = parse_s3(uri)
    s3 = s3_local()
    body = s3.get_object(Bucket=bkt, Key=key)["Body"].read()
    tmpdir = tempfile.mkdtemp(prefix="gdf_")
    path = os.path.join(tmpdir, "file.geojson")
    with open(path, "wb") as f:
        f.write(body)
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf
