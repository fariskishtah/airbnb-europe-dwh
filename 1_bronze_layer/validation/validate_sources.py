#!/usr/bin/env python
"""Validate the 20 raw source CSVs (existence, schema, MD5 vs Zenodo, no duplicates) without touching the DB."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from airbnb_dwh import bronze  # noqa: E402

if __name__ == "__main__":
    problems = bronze.validate_sources()
    m = bronze.build_manifest()
    print(f"files={len(m)} rows={sum(x.row_count for x in m):,} md5_verified={sum(bool(x.md5_verified) for x in m)}/{len(m)}")
    if problems:
        print("FAILED:\n - " + "\n - ".join(problems))
        sys.exit(1)
    print("Source validation PASSED")
