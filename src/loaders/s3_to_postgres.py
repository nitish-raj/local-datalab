from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg import sql

from domain.paths import ndvi_day_prefix
from utils.s3_utils import _s3_local, get_s3_object


def _json_text(raw: str | bytes) -> str:
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    if isinstance(raw, str):
        return raw
    raise TypeError(f"Expected S3 object body as str or bytes, got {type(raw)!r}")


@dataclass(slots=True)
class PostgresConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str
    schema: str = "raw"

    @classmethod
    def from_env(cls) -> PostgresConfig:
        return cls(
            host=os.environ.get("ANALYTICS_DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("ANALYTICS_DB_PORT", "5432")),
            dbname=os.environ.get("ANALYTICS_DB_NAME", "analytics"),
            user=os.environ.get("ANALYTICS_DB_USER", "analytics"),
            password=os.environ.get("ANALYTICS_DB_PASSWORD", "analytics"),
            schema=os.environ.get("ANALYTICS_DB_SCHEMA", "raw"),
        )


def _iter_ndvi_keys(bucket: str, prefix: str) -> list[str]:
    s3 = _s3_local()
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/ndvi.json"):
                keys.append(key)
    return keys


def _parse_ndvi_payload(
    bucket: str, key: str, payload: dict[str, Any]
) -> dict[str, Any]:
    item_datetime = payload.get("item_datetime")
    return {
        "aoi_id": str(payload["aoi_id"]),
        "observation_date": payload["date"],
        "status": str(payload["status"]),
        "mean_ndvi": payload.get("mean_ndvi"),
        "cloud_cover": payload.get("cloud_cover"),
        "item_datetime": item_datetime,
        "source_bucket": bucket,
        "source_key": key,
        "loaded_at": datetime.now(timezone.utc),
    }


def _ensure_table(connection: psycopg.Connection, schema: str) -> None:
    create_schema = sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(
        sql.Identifier(schema)
    )
    create_table = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {}.raw_ndvi_observations (
            aoi_id TEXT NOT NULL,
            observation_date DATE NOT NULL,
            status TEXT NOT NULL,
            mean_ndvi DOUBLE PRECISION,
            cloud_cover DOUBLE PRECISION,
            item_datetime TIMESTAMPTZ,
            source_bucket TEXT NOT NULL,
            source_key TEXT NOT NULL,
            loaded_at TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (aoi_id, observation_date)
        );
        """
    ).format(sql.Identifier(schema))
    with connection.cursor() as cursor:
        cursor.execute(create_schema)
        cursor.execute(create_table)


def _upsert_rows(
    connection: psycopg.Connection,
    schema: str,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0

    statement = sql.SQL(
        """
        INSERT INTO {}.raw_ndvi_observations (
            aoi_id,
            observation_date,
            status,
            mean_ndvi,
            cloud_cover,
            item_datetime,
            source_bucket,
            source_key,
            loaded_at
        )
        VALUES (
            %(aoi_id)s,
            %(observation_date)s,
            %(status)s,
            %(mean_ndvi)s,
            %(cloud_cover)s,
            %(item_datetime)s,
            %(source_bucket)s,
            %(source_key)s,
            %(loaded_at)s
        )
        ON CONFLICT (aoi_id, observation_date)
        DO UPDATE SET
            status = EXCLUDED.status,
            mean_ndvi = EXCLUDED.mean_ndvi,
            cloud_cover = EXCLUDED.cloud_cover,
            item_datetime = EXCLUDED.item_datetime,
            source_bucket = EXCLUDED.source_bucket,
            source_key = EXCLUDED.source_key,
            loaded_at = EXCLUDED.loaded_at;
        """
    ).format(sql.Identifier(schema))

    with connection.cursor() as cursor:
        cursor.executemany(statement, rows)

    return len(rows)


def sync_ndvi_from_s3_to_postgres(
    bucket: str,
    calc_prefix: str,
    day: str | None,
    postgres_config: PostgresConfig,
) -> dict[str, int]:
    if day:
        prefix = ndvi_day_prefix(calc_prefix, day)
    else:
        prefix = f"{calc_prefix.rstrip('/')}/aoi_timeseries/"

    keys = _iter_ndvi_keys(bucket=bucket, prefix=prefix)
    rows: list[dict[str, Any]] = []
    for key in keys:
        payload = json.loads(_json_text(get_s3_object(bucket=bucket, key=key)))
        rows.append(_parse_ndvi_payload(bucket=bucket, key=key, payload=payload))

    with psycopg.connect(
        host=postgres_config.host,
        port=postgres_config.port,
        dbname=postgres_config.dbname,
        user=postgres_config.user,
        password=postgres_config.password,
        autocommit=False,
    ) as connection:
        _ensure_table(connection, postgres_config.schema)
        inserted_rows = _upsert_rows(connection, postgres_config.schema, rows)
        connection.commit()

    return {
        "scanned_keys": len(keys),
        "upserted_rows": inserted_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load NDVI JSON artifacts from S3 into Postgres raw table"
    )
    parser.add_argument(
        "--bucket",
        default=os.environ.get("PROCESSED_AOI_BUCKET"),
        required=os.environ.get("PROCESSED_AOI_BUCKET") is None,
        help="Processed S3 bucket name",
    )
    parser.add_argument(
        "--calc-prefix",
        default=os.environ.get("PIPELINE_CALC_PREFIX", "calculation/"),
        help="Calculation prefix inside processed bucket",
    )
    parser.add_argument(
        "--day",
        default=None,
        help="Optional day in YYYY-MM-DD format to load only one partition",
    )
    args = parser.parse_args()

    outcome = sync_ndvi_from_s3_to_postgres(
        bucket=args.bucket,
        calc_prefix=args.calc_prefix,
        day=args.day,
        postgres_config=PostgresConfig.from_env(),
    )
    print(json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()
