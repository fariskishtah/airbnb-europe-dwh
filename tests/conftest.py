"""Integration fixtures: the whole pipeline is rebuilt from scratch into a dedicated TEST database."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "4_web_dashboard"))
TEST_URL = os.environ.get("AIRBNB_DWH_TEST_URL", "postgresql://127.0.0.1:54329/airbnb_dwh_test")
os.environ["AIRBNB_DWH_URL"] = TEST_URL   # must be set before dashboard/db modules read config

from airbnb_dwh import bronze, db, dq, gold, silver  # noqa: E402


@pytest.fixture(scope="session")
def silver_df(tmp_path_factory):
    out = tmp_path_factory.mktemp("silver")
    df, report = silver.build(out_dir=out)
    return df


@pytest.fixture(scope="session")
def warehouse(silver_df):
    """Drop everything, then run Bronze -> Silver -> Gold -> DQ against the test database."""
    try:
        conn = db.connect(TEST_URL)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"test PostgreSQL not reachable: {exc}")
    for s in ["gold", "gold_ref", "silver", "bronze", "meta"]:
        conn.execute(f"DROP SCHEMA IF EXISTS {s} CASCADE")
    conn.commit()
    manifest = bronze.build_manifest()
    run_id = bronze.new_run_id()
    with db.pipeline_step(conn, run_id, "bronze", "ingest_raw_csv") as h:
        stats = bronze.load_bronze(conn, manifest, run_id)
        h["rows"] = conn.execute("SELECT count(*) FROM bronze.raw_offers").fetchone()[0]
    with db.pipeline_step(conn, run_id, "silver", "clean_and_load_master") as h:
        h["rows"] = silver.load_to_postgres(conn, silver_df)
    with db.pipeline_step(conn, run_id, "gold", "build_star_schema") as h:
        counts = gold.build_gold(conn)
        h["rows"] = counts["fact_offer_observation"]
    checks = dq.run_checks(conn)
    dq.persist(conn, checks, run_id)
    conn.run_stats = {"bronze": stats, "gold": counts, "checks": checks}
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def _clean_transaction(request):
    """A failed statement in one test must never poison the shared connection for the next."""
    yield
    if "warehouse" in request.fixturenames:
        request.getfixturevalue("warehouse").rollback()
