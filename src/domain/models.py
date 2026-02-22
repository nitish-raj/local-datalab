from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PipelineConf:
    processed_bucket: str
    derived_out_prefix: str
    ingest_out_prefix: str
    calc_out_prefix: str
    aois_json_s3: str
    fields_with_aoi_s3: str

    def to_dict(self) -> dict:
        return {
            "processed_bucket": self.processed_bucket,
            "derived_out_prefix": self.derived_out_prefix,
            "ingest_out_prefix": self.ingest_out_prefix,
            "calc_out_prefix": self.calc_out_prefix,
            "aois_json_s3": self.aois_json_s3,
            "fields_with_aoi_s3": self.fields_with_aoi_s3,
        }

    @classmethod
    def from_dict(cls, data: dict) -> PipelineConf:
        return cls(
            processed_bucket=data["processed_bucket"],
            derived_out_prefix=data["derived_out_prefix"],
            ingest_out_prefix=data["ingest_out_prefix"],
            calc_out_prefix=data["calc_out_prefix"],
            aois_json_s3=data["aois_json_s3"],
            fields_with_aoi_s3=data["fields_with_aoi_s3"],
        )


@dataclass(slots=True)
class Aoi:
    aoi_id: str
    bbox: list[float]

    def to_dict(self) -> dict:
        return {
            "aoi_id": self.aoi_id,
            "bbox": list(self.bbox),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Aoi:
        return cls(
            aoi_id=data["aoi_id"],
            bbox=[float(v) for v in data["bbox"]],
        )


@dataclass(slots=True)
class IngestRef:
    aoi_id: str
    date: str
    status: str
    bbox: list[float]
    stac_url: str | None
    collection: str | None
    item_id: str | None
    b04_asset: str | None
    b08_asset: str | None
    cloud_cover: float | None
    item_datetime: str | None

    def to_dict(self) -> dict:
        return {
            "aoi_id": self.aoi_id,
            "date": self.date,
            "status": self.status,
            "bbox": list(self.bbox),
            "stac_url": self.stac_url,
            "collection": self.collection,
            "item_id": self.item_id,
            "b04_asset": self.b04_asset,
            "b08_asset": self.b08_asset,
            "cloud_cover": self.cloud_cover,
            "item_datetime": self.item_datetime,
        }

    @classmethod
    def from_dict(cls, data: dict) -> IngestRef:
        return cls(
            aoi_id=data["aoi_id"],
            date=data["date"],
            status=data["status"],
            bbox=[float(v) for v in data["bbox"]],
            stac_url=data.get("stac_url"),
            collection=data.get("collection"),
            item_id=data.get("item_id"),
            b04_asset=data.get("b04_asset"),
            b08_asset=data.get("b08_asset"),
            cloud_cover=(
                float(data["cloud_cover"])
                if data.get("cloud_cover") is not None
                else None
            ),
            item_datetime=data.get("item_datetime"),
        )


@dataclass(slots=True)
class NdviResult:
    aoi_id: str
    date: str
    status: str
    mean_ndvi: float | None
    cloud_cover: float | None
    item_datetime: str | None

    def to_dict(self) -> dict:
        return {
            "aoi_id": self.aoi_id,
            "date": self.date,
            "status": self.status,
            "mean_ndvi": self.mean_ndvi,
            "cloud_cover": self.cloud_cover,
            "item_datetime": self.item_datetime,
        }

    @classmethod
    def from_dict(cls, data: dict) -> NdviResult:
        return cls(
            aoi_id=data["aoi_id"],
            date=data["date"],
            status=data["status"],
            mean_ndvi=(
                float(data["mean_ndvi"]) if data.get("mean_ndvi") is not None else None
            ),
            cloud_cover=(
                float(data["cloud_cover"])
                if data.get("cloud_cover") is not None
                else None
            ),
            item_datetime=data.get("item_datetime"),
        )


@dataclass(slots=True)
class AoiWorkItem:
    aoi_id: str
    geom: dict

    def to_dict(self) -> dict:
        return {
            "aoi_id": self.aoi_id,
            "geom": dict(self.geom),
        }

    @classmethod
    def from_dict(cls, data: dict) -> AoiWorkItem:
        return cls(
            aoi_id=data["aoi_id"],
            geom=dict(data["geom"]),
        )
