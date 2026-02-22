import os
import tempfile

import boto3
import geopandas as gpd
from botocore.config import Config
from botocore.exceptions import ClientError


def _s3_local():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-central-1"),
        config=Config(s3={"addressing_style": "path"}),
    )


def _raise_s3_error(operation: str, bucket: str, key: str, exc: ClientError):
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    msg = exc.response.get("Error", {}).get("Message", str(exc))
    raise RuntimeError(
        f"S3 {operation} failed for s3://{bucket}/{key} [{code}]: {msg}"
    ) from exc


def download_s3_to_file(bucket: str, key: str, out_path: str):
    s3 = _s3_local()
    try:
        s3.download_file(Bucket=bucket, Key=key, Filename=out_path)
    except ClientError as exc:
        _raise_s3_error("download_file", bucket, key, exc)


def write_to_s3(bucket: str, key: str, data: bytes, content_type: str):
    s3 = _s3_local()
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    except ClientError as exc:
        _raise_s3_error("put_object", bucket, key, exc)


def get_s3_object(bucket: str, key: str) -> str:
    s3 = _s3_local()
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return response["Body"].read().decode()
    except ClientError as exc:
        _raise_s3_error("get_object", bucket, key, exc)


def s3_object_exists(bucket: str, key: str) -> bool:
    s3 = _s3_local()
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        code = str(exc.response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def parse_s3(uri: str):
    b, k = uri[5:].split("/", 1)
    return b, k


def read_gdf_from_s3(uri: str) -> gpd.GeoDataFrame:
    bkt, key = parse_s3(uri)
    tmpdir = tempfile.mkdtemp(prefix="gdf_")
    path = os.path.join(tmpdir, "file.geojson")
    download_s3_to_file(bucket=bkt, key=key, out_path=path)
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf
