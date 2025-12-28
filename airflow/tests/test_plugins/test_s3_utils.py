import os
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[3]
DAGS_DIR = REPO_DIR / "airflow" / "dags"
sys.path.insert(0, str(DAGS_DIR))

from plugins import s3_utils  # noqa: E402


def test_parse_s3():
    bucket, key = s3_utils.parse_s3("s3://my-bucket/path/to/file.txt")
    assert bucket == "my-bucket"
    assert key == "path/to/file.txt"


def test_s3_local_uses_endpoint_env():
    os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"
    client = s3_utils.s3_local()
    assert client.meta.endpoint_url == "http://localhost:4566"
