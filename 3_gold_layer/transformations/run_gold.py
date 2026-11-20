#!/usr/bin/env python
"""Rebuild the Gold star schema from Silver."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from airbnb_dwh import bronze, db, gold  # noqa: E402

if __name__ == "__main__":
    run_id = bronze.new_run_id()
    with db.connect() as conn:
        with db.pipeline_step(conn, run_id, "gold", "build_star_schema") as h:
            counts = gold.build_gold(conn)
            h["rows"] = counts["fact_offer_observation"]
            h["detail"] = ", ".join(f"{k}={v}" for k, v in counts.items())
    print("Gold OK:", h["detail"])
