# ruff: noqa: E402

import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from utils import s3_utils
from utils.s3_utils import _s3_local, get_s3_object, parse_s3, write_to_s3


def test_parse_s3():
    bucket, key = parse_s3("s3://my-bucket/path/to/file.txt")
    assert bucket == "my-bucket"
    assert key == "path/to/file.txt"


def test_s3_local_uses_endpoint_env(monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    client = _s3_local()
    assert client.meta.endpoint_url == "http://localhost:4566"


def test_s3_local_uses_default_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    captured = {}

    def fake_client(service_name, **kwargs):
        captured["service_name"] = service_name
        captured["kwargs"] = kwargs

        class Dummy:
            meta = type("Meta", (), {"endpoint_url": kwargs.get("endpoint_url")})()

        return Dummy()

    monkeypatch.setattr(s3_utils.boto3, "client", fake_client)

    _s3_local()

    assert captured["service_name"] == "s3"
    assert captured["kwargs"]["endpoint_url"] == "http://localhost:4566"
    assert captured["kwargs"]["aws_access_key_id"] == "test"
    assert captured["kwargs"]["aws_secret_access_key"] == "test"
    assert captured["kwargs"]["region_name"] == "eu-central-1"


def test_write_to_s3_uses_client(monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    called = {}

    class DummyClient:
        def put_object(self, **kwargs):
            called.update(kwargs)

    monkeypatch.setattr(
        s3_utils.boto3, "client", lambda *_args, **_kwargs: DummyClient()
    )

    write_to_s3("my-bucket", "path/file.txt", b"data", "text/plain")

    assert called["Bucket"] == "my-bucket"
    assert called["Key"] == "path/file.txt"
    assert called["Body"] == b"data"
    assert called["ContentType"] == "text/plain"


def test_get_s3_object_returns_text(monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")

    class DummyBody:
        def read(self):
            return b"hello"

    class DummyClient:
        def get_object(self, **_kwargs):
            return {"Body": DummyBody()}

    monkeypatch.setattr(
        s3_utils.boto3, "client", lambda *_args, **_kwargs: DummyClient()
    )

    result = get_s3_object("my-bucket", "path/file.txt")

    assert result == "hello"


def test_parse_s3_handles_nested_paths():
    bucket, key = parse_s3("s3://bucket/some/deep/path/file.geojson")
    assert bucket == "bucket"
    assert key == "some/deep/path/file.geojson"
