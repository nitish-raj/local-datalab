# ruff: noqa: E402

import json
import sys
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[2]
DAGS_DIR = REPO_DIR / "orchestrator" / "dags"
SRC_DIR = REPO_DIR / "src"
sys.path.insert(0, str(DAGS_DIR))
sys.path.insert(0, str(SRC_DIR))

from loaders import s3_to_postgres
from loaders.s3_to_postgres import PostgresConfig


class _FakeConnection:
    def __init__(self):
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        self.committed = True


def test_postgres_config_from_env(monkeypatch):
    monkeypatch.setenv("ANALYTICS_DB_HOST", "postgres.local")
    monkeypatch.setenv("ANALYTICS_DB_PORT", "6543")
    monkeypatch.setenv("ANALYTICS_DB_NAME", "warehouse")
    monkeypatch.setenv("ANALYTICS_DB_USER", "warehouse_user")
    monkeypatch.setenv("ANALYTICS_DB_PASSWORD", "warehouse_password")
    monkeypatch.setenv("ANALYTICS_DB_SCHEMA", "raw_ingest")

    config = PostgresConfig.from_env()

    assert config.host == "postgres.local"
    assert config.port == 6543
    assert config.dbname == "warehouse"
    assert config.user == "warehouse_user"
    assert config.password == "warehouse_password"
    assert config.schema == "raw_ingest"


def test_sync_ndvi_from_s3_to_postgres_upserts_rows(monkeypatch):
    monkeypatch.setattr(
        s3_to_postgres,
        "_iter_ndvi_keys",
        lambda bucket, prefix: [
            "calculation/aoi_timeseries/date=2025-12-01/aoi_id=AOI_01/ndvi.json",
            "calculation/aoi_timeseries/date=2025-12-01/aoi_id=AOI_02/ndvi.json",
        ],
    )

    payloads = {
        "calculation/aoi_timeseries/date=2025-12-01/aoi_id=AOI_01/ndvi.json": {
            "aoi_id": "AOI_01",
            "date": "2025-12-01",
            "status": "ok",
            "mean_ndvi": 0.71,
            "cloud_cover": 11.2,
            "item_datetime": "2025-12-01T10:00:00Z",
        },
        "calculation/aoi_timeseries/date=2025-12-01/aoi_id=AOI_02/ndvi.json": {
            "aoi_id": "AOI_02",
            "date": "2025-12-01",
            "status": "missing_crs",
            "mean_ndvi": None,
        },
    }
    monkeypatch.setattr(
        s3_to_postgres,
        "get_s3_object",
        lambda bucket, key: json.dumps(payloads[key]),
    )

    fake_connection = _FakeConnection()
    monkeypatch.setattr(s3_to_postgres.psycopg, "connect", lambda **_: fake_connection)

    ensured = {"value": False}
    monkeypatch.setattr(
        s3_to_postgres,
        "_ensure_table",
        lambda connection, schema: ensured.update(value=True),
    )

    captured = {"rows": 0, "schema": None}

    def fake_upsert(connection, schema, rows):
        captured["rows"] = len(rows)
        captured["schema"] = schema
        return len(rows)

    monkeypatch.setattr(s3_to_postgres, "_upsert_rows", fake_upsert)

    outcome = s3_to_postgres.sync_ndvi_from_s3_to_postgres(
        bucket="processed-aoi-data",
        calc_prefix="calculation/",
        day="2025-12-01",
        postgres_config=PostgresConfig(
            host="127.0.0.1",
            port=5432,
            dbname="analytics",
            user="analytics",
            password="analytics",
            schema="raw",
        ),
    )

    assert ensured["value"] is True
    assert captured["rows"] == 2
    assert captured["schema"] == "raw"
    assert fake_connection.committed is True
    assert outcome == {"scanned_keys": 2, "upserted_rows": 2}
