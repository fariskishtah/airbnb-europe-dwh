#!/usr/bin/env python
"""Silver build: clean raw CSVs -> data/silver master (parquet+csv) -> silver.airbnb_europe_master."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from airbnb_dwh import bronze, db, silver  # noqa: E402

if __name__ == "__main__":
    run_id = bronze.new_run_id()
    df, report = silver.build()
    with db.connect() as conn:
        conn.execute(open(Path(__file__).resolve().parents[2] / "3_gold_layer/ddl/01_bronze_silver_tables.sql").read())
        conn.commit()
        with db.pipeline_step(conn, run_id, "silver", "clean_and_load_master") as h:
            n = silver.load_to_postgres(conn, df)
            bronze_n = conn.execute("SELECT count(*) FROM bronze.raw_offers").fetchone()[0]
            h["rows"] = n
            h["detail"] = f"bronze={bronze_n} silver={n} quarantined={report['rows_quarantined']}"
    print(json.dumps(report, indent=2))
    print("Silver OK:", h["detail"])
