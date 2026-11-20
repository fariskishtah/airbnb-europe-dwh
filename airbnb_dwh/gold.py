"""Gold layer builder: (re)create the star schema from Silver in PostgreSQL, using the SQL scripts."""
from __future__ import annotations

from . import config, db
from .reference import CITY_REFERENCE


def build_gold(conn) -> dict:
    db.run_sql_file(conn, config.DDL_DIR / "01_bronze_silver_tables.sql")
    db.run_sql_file(conn, config.DDL_DIR / "00_reference_tables.sql")
    conn.execute("TRUNCATE gold_ref.city_reference")
    for k, (disp, country, lat, lng) in CITY_REFERENCE.items():
        conn.execute("INSERT INTO gold_ref.city_reference VALUES (%s,%s,%s,%s,%s)", (k, disp, country, lat, lng))
    db.run_sql_file(conn, config.DDL_DIR / "02_gold_star_schema.sql")
    db.run_sql_file(conn, config.TRANSFORM_DIR / "10_load_dimensions_and_fact.sql")
    db.run_sql_file(conn, config.DDL_DIR / "03_gold_views.sql")
    conn.commit()
    counts = {}
    for t in ["dim_city", "dim_day_type", "dim_room_type", "dim_host_status", "dim_source_file", "fact_offer_observation"]:
        counts[t] = conn.execute(f"SELECT count(*) FROM gold.{t}").fetchone()[0]
    return counts
