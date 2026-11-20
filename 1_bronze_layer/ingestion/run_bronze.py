#!/usr/bin/env python
"""Bronze ingestion: validate sources, write manifest, load raw text into PostgreSQL (idempotent)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from airbnb_dwh import bronze, db  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="reload files even if hash unchanged")
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()
    run_id = args.run_id or bronze.new_run_id()
    problems = bronze.validate_sources()
    if problems:
        print("SOURCE VALIDATION FAILED:\n - " + "\n - ".join(problems))
        return 1
    manifest = bronze.build_manifest()
    bronze.write_manifest(manifest, run_id)
    with db.connect() as conn:
        with db.pipeline_step(conn, run_id, "bronze", "ingest_raw_csv") as h:
            stats = bronze.load_bronze(conn, manifest, run_id, force=args.force)
            total = conn.execute("SELECT count(*) FROM bronze.raw_offers").fetchone()[0]
            h["rows"], h["detail"] = total, f"loaded={len(stats['loaded'])} skipped={len(stats['skipped'])} replaced={len(stats['replaced'])}"
    print(f"Bronze OK: {len(manifest)} files, {total:,} rows in bronze.raw_offers | {h['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
