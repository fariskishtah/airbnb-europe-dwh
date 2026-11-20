"""Automated data-quality checks across Bronze / Silver / Gold. Every result is computed, never hard-coded."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from . import bronze, config
from .reference import MAX_COORD_OFFSET_DEG


@dataclass
class Check:
    layer: str
    name: str
    expected: str
    actual: str
    status: str  # PASS / FAIL
    detail: str = ""


def _scalar(conn, sql: str, *args):
    return conn.execute(sql, args).fetchone()[0]


def run_checks(conn) -> list[Check]:
    out: list[Check] = []

    def add(layer, name, expected, actual, ok, detail=""):
        out.append(Check(layer, name, str(expected), str(actual), "PASS" if ok else "FAIL", detail))

    # ---- Bronze
    files = bronze.discover()
    add("bronze", "20 raw CSV files present on disk", 20, len(files), len(files) == 20)
    n_log = _scalar(conn, "SELECT count(*) FROM bronze.ingestion_log")
    add("bronze", "20 files registered in ingestion_log", 20, n_log, n_log == 20)
    verified = _scalar(conn, "SELECT count(*) FROM bronze.ingestion_log WHERE md5_verified IS TRUE")
    add("bronze", "File MD5 matches Zenodo record", 20, verified, verified == 20)
    dup_sha = _scalar(conn, "SELECT count(*) - count(DISTINCT sha256) FROM bronze.ingestion_log")
    add("bronze", "No duplicate file ingestion (SHA-256)", 0, dup_sha, dup_sha == 0)
    bad_rows = _scalar(conn, """SELECT count(*) FROM (SELECT l.source_file FROM bronze.ingestion_log l
        LEFT JOIN bronze.raw_offers r USING(source_file) GROUP BY l.source_file, l.row_count
        HAVING count(r.*) <> l.row_count) x""")
    add("bronze", "Bronze rows per file equal source row count", 0, bad_rows, bad_rows == 0)
    raw_nulls = _scalar(conn, """SELECT count(*) FROM bronze.raw_offers WHERE realsum IS NULL OR room_type IS NULL
        OR lat IS NULL OR lng IS NULL OR realsum = '' OR lat = ''""")
    add("bronze", "No null/blank key fields in raw rows", 0, raw_nulls, raw_nulls == 0)
    # ---- Silver
    b = _scalar(conn, "SELECT count(*) FROM bronze.raw_offers")
    s = _scalar(conn, "SELECT count(*) FROM silver.airbnb_europe_master")
    add("silver", "Bronze -> Silver row reconciliation", b, s, b == s, "no row loss and no expansion")
    d = _scalar(conn, "SELECT count(*) - count(DISTINCT offer_id) FROM silver.airbnb_europe_master")
    add("silver", "Unique offer_id (source-row lineage)", 0, d, d == 0)
    lin = _scalar(conn, """SELECT count(*) FROM silver.airbnb_europe_master s LEFT JOIN bronze.raw_offers r
        ON r.source_file=s.source_file AND r.source_row_index::int = s.source_row_index WHERE r.source_file IS NULL""")
    add("silver", "Every Silver row traces back to a Bronze row", 0, lin, lin == 0)
    drift = _scalar(conn, """SELECT count(*) FROM silver.airbnb_europe_master s JOIN bronze.raw_offers r
        ON r.source_file=s.source_file AND r.source_row_index::int = s.source_row_index
        WHERE abs(s.real_sum - r.realsum::float8) > 1e-9""")
    add("silver", "Silver real_sum equals Bronze realSum (no value drift)", 0, drift, drift == 0)
    chk = {
        "Prices strictly positive": "real_sum <= 0",
        "Satisfaction within 0-100": "guest_satisfaction_overall NOT BETWEEN 0 AND 100",
        "Cleanliness within 0-10": "cleanliness_rating NOT BETWEEN 0 AND 10",
        "Capacity >= 1 and bedrooms >= 0": "person_capacity < 1 OR bedrooms < 0",
        "Distances non-negative": "dist_city_center_km < 0 OR dist_metro_km < 0",
        "Valid room types": "room_type NOT IN ('Entire home/apt','Private room','Shared room')",
        "Nightly equivalent = two-night total / 2": "abs(nightly_equivalent_eur*2 - two_night_total_eur) > 1e-9",
    }
    for name, cond in chk.items():
        n = _scalar(conn, f"SELECT count(*) FROM silver.airbnb_europe_master WHERE {cond}")
        add("silver", name, 0, n, n == 0, "violating rows")
    far = _scalar(conn, """SELECT count(*) FROM silver.airbnb_europe_master s JOIN gold_ref.city_reference r ON r.display_name=s.city
        WHERE abs(s.lat-r.lat) > %s OR abs(s.lng-r.lng) > %s""", MAX_COORD_OFFSET_DEG, MAX_COORD_OFFSET_DEG)
    add("silver", "Coordinates within reference city bounding box", 0, far, far == 0)
    # ---- Gold
    g = _scalar(conn, "SELECT count(*) FROM gold.fact_offer_observation")
    add("gold", "Silver -> Gold fact row reconciliation", s, g, s == g)
    sp = _scalar(conn, "SELECT sum(two_night_total_eur) FROM silver.airbnb_europe_master")
    gp = _scalar(conn, "SELECT sum(two_night_total_eur) FROM gold.fact_offer_observation")
    add("gold", "Silver -> Gold price sum reconciliation", f"{sp:.6f}", f"{gp:.6f}", abs(sp - gp) < 1e-6)
    for dim, key in [("dim_city", "city_key"), ("dim_day_type", "day_type_key"), ("dim_room_type", "room_type_key"),
                     ("dim_host_status", "host_status_key"), ("dim_source_file", "source_file_key")]:
        n = _scalar(conn, f"SELECT count(*) FROM gold.fact_offer_observation f LEFT JOIN gold.{dim} d USING({key}) WHERE d.{key} IS NULL")
        add("gold", f"Fact -> {dim} referential integrity", 0, n, n == 0, "orphan fact rows")
    dupg = _scalar(conn, "SELECT count(*) - count(DISTINCT (source_file_key, source_row_index)) FROM gold.fact_offer_observation")
    add("gold", "Fact grain unique (source file, source row)", 0, dupg, dupg == 0)
    fks = _scalar(conn, "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='gold' AND c.contype='f'")
    add("gold", "Foreign keys declared in database", 7, fks, fks == 7, "5 on fact_offer_observation + 2 on dim_source_file")
    pks = _scalar(conn, "SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='gold' AND c.contype='p'")
    add("gold", "Primary keys declared (6 tables)", 6, pks, pks == 6)
    sf = _scalar(conn, "SELECT count(*) FROM gold.dim_source_file d JOIN (SELECT source_file_key, count(*) c FROM gold.fact_offer_observation GROUP BY 1) f USING(source_file_key) WHERE f.c <> d.source_row_count")
    add("gold", "Fact rows per source file equal source row count", 0, sf, sf == 0)
    return out


def persist(conn, checks: list[Check], run_id: str) -> None:
    conn.execute("CREATE SCHEMA IF NOT EXISTS meta")
    conn.execute("""CREATE TABLE IF NOT EXISTS meta.dq_result(id bigserial PRIMARY KEY, run_id text NOT NULL, layer text NOT NULL,
        check_name text NOT NULL, expected text, actual text, status text NOT NULL, detail text, checked_at timestamptz NOT NULL DEFAULT now())""")
    for c in checks:
        conn.execute("INSERT INTO meta.dq_result(run_id,layer,check_name,expected,actual,status,detail) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                     (run_id, c.layer, c.name, c.expected, c.actual, c.status, c.detail))
    conn.commit()
    config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (config.REPORT_DIR / "data_quality_report.json").write_text(json.dumps({
        "run_id": run_id, "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "passed": sum(c.status == "PASS" for c in checks), "failed": sum(c.status == "FAIL" for c in checks),
        "checks": [asdict(c) for c in checks]}, indent=2))
