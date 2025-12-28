import os
import sys
from pathlib import Path

from airflow.models import DagBag


REPO_DIR = Path(__file__).resolve().parents[3]
DAGS_DIR = REPO_DIR / "airflow" / "dags"


def test_dags_import_without_errors():
    # Ensure DAG-local plugin imports resolve
    sys.path.insert(0, str(DAGS_DIR))

    dagbag = DagBag(dag_folder=str(DAGS_DIR), include_examples=False)
    assert dagbag.import_errors == {}

    expected = {
        "calculate_daily_ndvi",
        "ingest_sentinel2_data",
        "simulate_aoi_from_fields",
    }
    assert expected.issubset(set(dagbag.dag_ids))
