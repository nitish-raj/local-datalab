min# Data Flow And Abstraction Improvements Plan

## Why This Document Exists

This plan translates the feedback:

"Data flow convoluted for the sake of a PoC -> missing the right level of abstraction"

into an actionable, low-risk refactor roadmap for this repository.

The goal is **not** to rewrite everything. The goal is to make the pipeline easy to understand, test, and evolve while preserving current behavior.

---

## Current State Summary (What Is Hard To Follow)

### 1) DAG files combine too many concerns

- `airflow/dags/01_simulate_aoi_from_fields.py`
  - Orchestration (Airflow DAG + task wiring)
  - Domain logic (AOI clustering with DBSCAN)
  - Storage concerns (S3 read/write keys)
  - Cross-DAG control flow (`TriggerDagRunOperator`)

- `airflow/dags/02_ingest_sentinel2_data.py`
  - Orchestration + backfill-day planning + STAC query logic + S3 idempotency checks
  - Business rules and storage layout details are mixed in one place

- `airflow/dags/03_calculate_daily_ndvi.py`
  - Orchestration + raster compute + STAC lookups + output persistence in one module

### 2) Weak data contracts between steps

- Cross-DAG payloads are generic dicts (`conf["..."]`) with implicit keys.
- Missing typed contracts means key names and schema assumptions are spread across multiple DAGs.

### 3) Path/key conventions are duplicated

- `derived/`, `ingest/`, `calculation/` keys are built in multiple places.
- Small naming changes can break multiple tasks because there is no central path builder.

### 4) Idempotency checks are distributed and low-level

- `s3_object_exists` checks appear in multiple loops.
- Existence checks are performed at DAG/service logic level instead of repository boundary.

### 5) Utility surface is too low-level for DAG usage

- `airflow/dags/utils/s3_utils.py` is a good primitive layer, but DAGs still need higher-level repository methods.
- Example: `get_s3_object` is typed as `bytes` but returns decoded text; this is a subtle contract mismatch.

---

## Target End State

## What "Right Abstraction" Means Here

- DAG files should answer: **what runs, when, and in which dependency order**.
- Service modules should answer: **how business/domain work is computed**.
- Repository modules should answer: **where and how artifacts are persisted**.
- Data models should answer: **what payload shape is valid between stages**.

## Desired Properties

- New contributor can understand full flow in <15 minutes.
- Most logic can be unit tested without running Airflow.
- Key/path conventions are defined once.
- Step outputs are schema-validated and explicit.

---

## Proposed Project Structure (Incremental)

Add the following package layout under `airflow/dags/`:

```text
airflow/dags/
  domain/
    models.py          # typed payloads and artifact schemas
    paths.py           # S3 key/path builders
  repositories/
    artifact_repo.py   # high-level S3 read/write/check methods
  services/
    aoi_service.py     # AOI inference and field tagging
    stac_service.py    # STAC search and reference selection
    ndvi_service.py    # NDVI computation from references
  utils/
    s3_utils.py        # keep as low-level primitive API
```

Notes:

- Keep existing DAG file names and DAG IDs unchanged to avoid deployment impact.
- Move logic behind small functions first; then simplify DAG files.

---

## Data Contracts To Introduce

Use dataclasses first (minimal dependency), then consider Pydantic only if runtime validation is needed.

### `domain/models.py`

Suggested models:

1. `PipelineConf`
   - `processed_bucket: str`
   - `derived_out_prefix: str`
   - `ingest_out_prefix: str`
   - `calc_out_prefix: str`
   - `aois_json_s3: str`
   - `fields_with_aoi_s3: str`

2. `Aoi`
   - `aoi_id: str`
   - `bbox: list[float]`  # [minlon, minlat, maxlon, maxlat]

3. `IngestRef`
   - `aoi_id: str`
   - `date: str`
   - `status: str` (`ok`, `no_items`, etc.)
   - `bbox: list[float]`
   - `stac_url: str | None`
   - `collection: str | None`
   - `item_id: str | None`
   - `b04_asset: str | None`
   - `b08_asset: str | None`
   - `cloud_cover: float | None`
   - `item_datetime: str | None`

4. `NdviResult`
   - `aoi_id: str`
   - `date: str`
   - `status: str`
   - `mean_ndvi: float | None`
   - `cloud_cover: float | None`
   - `item_datetime: str | None`

5. `AoiWorkItem`
   - `aoi_id: str`
   - `geom: dict`  # geo interface payload

Include conversion helpers:

- `from_dict(...)`
- `to_dict(...)`

This avoids ad-hoc dictionary key usage in DAG code.

---

## Centralize Storage Layout

### `domain/paths.py`

Create deterministic path builders:

- `aois_key(derived_prefix) -> str`
- `fields_with_aoi_key(derived_prefix) -> str`
- `ingest_ref_key(ingest_prefix, aoi_id, day) -> str`
- `ndvi_key(calc_prefix, aoi_id, day) -> str`
- `ndvi_day_prefix(calc_prefix, day) -> str`

Rules:

- Normalize prefixes once: `prefix.rstrip('/') + '/'`.
- Never build key strings directly in DAG/service code.
- Keep exact existing key format for backward compatibility.

---

## Add Repository Layer

### `repositories/artifact_repo.py`

Wrap low-level `utils/s3_utils.py` with domain methods:

- AOI artifacts
  - `read_aois(s3_uri) -> list[Aoi]`
  - `write_aois(bucket, key, aois)`
  - `read_fields_with_aoi(s3_uri) -> GeoDataFrame`
  - `write_fields_with_aoi(bucket, key, fields_gdf)`

- Ingest artifacts
  - `ingest_ref_exists(bucket, ingest_prefix, aoi_id, day) -> bool`
  - `read_ingest_ref(bucket, ingest_prefix, aoi_id, day) -> IngestRef`
  - `write_ingest_ref(bucket, ingest_prefix, ref: IngestRef)`

- NDVI artifacts
  - `ndvi_exists(bucket, calc_prefix, aoi_id, day) -> bool`
  - `write_ndvi_result(bucket, calc_prefix, result: NdviResult)`

Benefits:

- DAG logic stops handling `bucket/key` and serialization details.
- Idempotency logic has one owner.

---

## Service Layer Split

### 1) `services/aoi_service.py`

Move these responsibilities from `01_simulate_aoi_from_fields.py`:

- CRS normalization
- centroid extraction
- eps estimation
- DBSCAN clustering
- noise reassignment
- AOI bbox generation
- output field tagging

Target signature:

`infer_aois_and_tag_fields(fields_gdf, min_cluster_size, eps_quantile, padding_m) -> tuple[list[Aoi], GeoDataFrame]`

### 2) `services/stac_service.py`

Move from `02_ingest_sentinel2_data.py`:

- STAC client open
- search query by bbox/date/cloud threshold
- best-item selection
- asset ID resolution
- conversion to `IngestRef`

Target signatures:

- `pick_asset_id(item, candidates) -> str`
- `fetch_ingest_ref(aoi: Aoi, day: str, max_cloud: float, stac_url: str, collection: str) -> IngestRef`

### 3) `services/ndvi_service.py`

Move from `03_calculate_daily_ndvi.py`:

- STAC item retrieval from reference
- stackstac loading
- raster masking
- NDVI computation
- result mapping to `NdviResult`

Target signatures:

- `compute_ndvi_for_aoi(geometry, ref: IngestRef) -> NdviResult`
- helper `pick_epsg`, `rasterize_geom_mask`, etc.

---

## DAG Simplification Plan

## Guiding Rule

Each DAG task should be mostly orchestration glue calling a service/repository function.

### DAG 01 (`01_simulate_aoi_from_fields`)

Current task does everything.

Target split inside DAG file:

1. `load_inputs()`
   - read fields from raw bucket
2. `infer_aois()`
   - call `aoi_service`
3. `persist_derived()`
   - call `artifact_repo`
4. `trigger_ingest()`
   - send typed `PipelineConf`

### DAG 02 (`02_ingest_sentinel2_data`)

Keep dynamic mapping, simplify internals:

1. `read_pipeline_conf()`
2. `plan_missing_days()`
   - move day planning into service/repo helper
3. `ingest_day(day)`
   - for each AOI: repo exists -> stac service -> repo write
4. `trigger_ndvi(day_payload)`

### DAG 03 (`03_calculate_daily_ndvi`)

1. `read_pipeline_conf()`
2. `build_aoi_work(day)`
   - this function should only decide *which AOIs* to process
3. `compute_aoi_ndvi(work_item)`
   - delegate compute to `ndvi_service`
4. `persist_daily_ndvi(results)`
   - write through repository only

---

## Optional Flow Simplification For PoC

If your objective is demo clarity over pipeline modularity, use one DAG with `TaskGroup`s:

- `TaskGroup("prepare")`: simulate AOIs + write derived
- `TaskGroup("ingest")`: ingest refs for date range
- `TaskGroup("compute")`: NDVI for eligible AOIs

Benefits:

- Fewer cross-DAG handoffs
- Easier UI traceability in Airflow

Tradeoff:

- Less independent re-run control per stage

Recommendation:

- Keep current 3-DAG split now (lower risk), but use typed conf + services so complexity is hidden.

---

## Detailed Execution Roadmap (PR-by-PR)

## PR 1 - Add Contracts And Paths (No behavior change)

Files:

- `airflow/dags/domain/models.py` (new)
- `airflow/dags/domain/paths.py` (new)

Tasks:

- Add dataclasses and `to_dict/from_dict` helpers.
- Add path/key builders preserving current key formats.
- Add unit tests for path generation and model serialization.

Done criteria:

- No DAG behavior changes.
- 100% test pass.

## PR 2 - Add Repository Layer (No behavior change)

Files:

- `airflow/dags/repositories/artifact_repo.py` (new)
- `airflow/tests/test_plugins/test_s3_utils.py` (extend)
- `airflow/tests/test_repositories/test_artifact_repo.py` (new)

Tasks:

- Wrap low-level S3 functions in domain-friendly methods.
- Add explicit JSON encode/decode and content type handling.
- Fix typing mismatch around `get_s3_object` usage by handling text/bytes explicitly in repo.

Done criteria:

- Repository methods cover all current artifact interactions.
- Existing DAGs can still run untouched.

## PR 3 - Extract AOI Service

Files:

- `airflow/dags/services/aoi_service.py` (new)
- `airflow/dags/01_simulate_aoi_from_fields.py` (refactor)
- `airflow/tests/test_services/test_aoi_service.py` (new)

Tasks:

- Move `infer_aois_and_tag_fields` to service.
- Keep DAG task body mostly orchestration + repository calls.
- Validate output schema parity with existing artifacts.

Done criteria:

- Artifact keys and payloads unchanged.
- Existing downstream DAGs require no changes.

## PR 4 - Extract STAC Service

Files:

- `airflow/dags/services/stac_service.py` (new)
- `airflow/dags/02_ingest_sentinel2_data.py` (refactor)
- `airflow/tests/test_services/test_stac_service.py` (new)

Tasks:

- Move `pick_asset_id` and STAC selection logic.
- Convert payload creation to typed `IngestRef`.
- Keep idempotency check via repository method.

Done criteria:

- Ingest JSON artifacts remain backward compatible.

## PR 5 - Extract NDVI Service

Files:

- `airflow/dags/services/ndvi_service.py` (new)
- `airflow/dags/03_calculate_daily_ndvi.py` (refactor)
- `airflow/tests/test_services/test_ndvi_service.py` (new)

Tasks:

- Move raster/stackstac/ndvi logic out of DAG.
- DAG function now orchestrates work expansion only.
- Preserve all output fields in NDVI JSON.

Done criteria:

- No output shape regression.
- Error statuses (`missing_crs`, `no_satellite_item`) preserved.

## PR 6 - Normalize Day Planning + Idempotency

Files:

- `airflow/dags/services/planning_service.py` (new, optional)
- `airflow/dags/02_ingest_sentinel2_data.py` (refactor)

Tasks:

- Move day-range and missing-day logic into one helper.
- Ensure idempotency checks are repository-owned.

Done criteria:

- Day planning is deterministic and covered by tests.

## PR 7 - Documentation And Dev Guide

Files:

- `README.md` (update)
- `AGENTS.md` (update if needed)

Tasks:

- Add architecture section with "DAG vs Service vs Repository" responsibilities.
- Add "How to add a new pipeline step" guide.

Done criteria:

- New contributor can onboard using docs only.

---

## Testing Strategy (Granular)

### Unit tests (fast)

- `test_domain_models.py`
  - serialization and validation of all model classes
- `test_paths.py`
  - all key-building invariants
- `test_aoi_service.py`
  - one-field, multi-field, noise-cluster edge cases
- `test_stac_service.py`
  - no items, asset key variants, cloud sorting
- `test_ndvi_service.py`
  - missing CRS, all-NaN NDVI, raster orientation handling

### Repository tests

- Mock S3 client and verify:
  - keys written correctly
  - content type set correctly
  - existence checks and read behavior

### DAG import tests

- Keep `airflow/tests/test_dags/test_dag_imports.py` as-is but ensure it still recognizes all DAG IDs.

### Integration smoke (optional but useful)

- run `01` then `02` then `03` against localstack with a tiny sample input.
- validate generated S3 objects exist at expected keys.

---

## Compatibility Rules During Refactor

- Do not change DAG IDs.
- Do not change output key formats during initial refactor.
- Do not change JSON schema fields in `s2_refs.json` and `ndvi.json` in first pass.
- Keep `TriggerDagRunOperator` behavior until service extraction is complete.

---

## Risks And Mitigations

1. Risk: Silent payload/schema drift between DAGs
   - Mitigation: typed model conversion + schema parity tests

2. Risk: Path/key regressions
   - Mitigation: central `paths.py` + golden tests for expected keys

3. Risk: Performance regressions in NDVI step
   - Mitigation: keep `max_active_tis_per_dag=2`, benchmark before/after with same data

4. Risk: Increased refactor size
   - Mitigation: small PR slices above, each behavior-preserving

---

## Definition Of Done

Refactor is considered complete when:

- DAG files are orchestration-first and significantly shorter.
- Domain logic is under `services/` and test-covered.
- Storage handling is under `repositories/` and test-covered.
- Key/path patterns are generated only by `domain/paths.py`.
- CI continues to pass existing DAG/plugin tests.

---

## Quick Start Checklist

Use this checklist while implementing:

- [ ] Add `domain/models.py` and `domain/paths.py`
- [ ] Add tests for models and paths
- [ ] Add `repositories/artifact_repo.py`
- [ ] Migrate DAG 01 to `aoi_service + artifact_repo`
- [ ] Migrate DAG 02 to `stac_service + artifact_repo`
- [ ] Migrate DAG 03 to `ndvi_service + artifact_repo`
- [ ] Keep output schema and key format stable
- [ ] Run:
  - `python -m pytest airflow/tests/test_dags/ -v`
  - `python -m pytest airflow/tests/test_plugins/ -v`
- [ ] Add/verify new service and repository tests
- [ ] Update README architecture section

---

## Suggested First Implementation Slice (1-2 days)

If you want immediate clarity gains with minimal risk, do only this first:

1. Add `domain/paths.py` and replace all inline key string formatting.
2. Add `PipelineConf` model and replace free-form dict usage for conf payload.
3. Move AOI inference function into `services/aoi_service.py`.

This alone will remove a large amount of cognitive load while preserving behavior.
