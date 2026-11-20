#!/usr/bin/env python
"""Execute every analytics_queries/*.sql and save results to artifacts/reports/analytics/*.csv."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from airbnb_dwh import db  # noqa: E402

if __name__ == "__main__":
    out = ROOT / "artifacts/reports/analytics"
    out.mkdir(parents=True, exist_ok=True)
    eng = db.engine()
    for f in sorted(Path(__file__).parent.glob("*.sql")):
        df = pd.read_sql(f.read_text(), eng)
        df.to_csv(out / f"{f.stem}.csv", index=False)
        print(f"== {f.stem} ({len(df)} rows)")
        print(df.to_string(index=False)[:1500])
