#!/usr/bin/env python
"""Run all data-quality checks; exit non-zero if any fails."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from airbnb_dwh import bronze, db, dq  # noqa: E402

if __name__ == "__main__":
    run_id = bronze.new_run_id()
    with db.connect() as conn:
        checks = dq.run_checks(conn)
        dq.persist(conn, checks, run_id)
    for c in checks:
        print(f"[{c.status}] {c.layer:6} {c.name}: expected={c.expected} actual={c.actual}")
    failed = [c for c in checks if c.status == "FAIL"]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    sys.exit(1 if failed else 0)
