#!/usr/bin/env python
"""Independently recompute KPIs from the Silver parquet (pandas) and compare with Gold SQL views and with the
dashboard's own query layer. Writes artifacts/reports/numeric_validation.json and .md. Exit 1 on any mismatch."""
import json
import logging
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "4_web_dashboard"))
logging.disable(logging.WARNING)
from airbnb_dwh import config, db  # noqa: E402
from components import data  # noqa: E402

TOL = 1e-9
s = pd.read_parquet(config.SILVER_DIR / "airbnb_europe_master.parquet")
eng = db.engine()
gold = lambda sql: pd.read_sql(sql, eng)  # noqa: E731
opt = data.dimension_options()
F = data.Filters(cities=opt["cities"], day_types=opt["days"], room_types=opt["rooms"], superhost=[True, False],
                 price_min=0, price_max=1e9, cap_min=1, cap_max=99)
rows = []


def cmp(name, silver_v, gold_v, dash_v):
    ok = all(math.isclose(float(silver_v), float(x), rel_tol=TOL, abs_tol=1e-9) for x in (gold_v, dash_v))
    rows.append({"kpi": name, "silver_pandas": float(silver_v), "gold_sql": float(gold_v), "dashboard_query": float(dash_v), "match": ok})


g = data.run("SELECT count(*) n, avg(two_night_total_eur) a, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) m, "
             "avg(guest_satisfaction_overall) sat, avg(cleanliness_rating) cl, avg(nightly_equivalent_eur) ne FROM gold.vw_offers_enriched WHERE {WHERE}", F).iloc[0]
gq = gold("SELECT count(*) n, avg(two_night_total_eur) a, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) m, "
          "avg(guest_satisfaction_overall) sat, avg(cleanliness_rating) cl, avg(nightly_equivalent_eur) ne FROM gold.fact_offer_observation").iloc[0]
for k, name, v in [("n", "total observations", len(s)), ("a", "avg two-night total", s.two_night_total_eur.mean()), ("m", "median two-night total", s.two_night_total_eur.median()),
                   ("sat", "avg satisfaction", s.guest_satisfaction_overall.mean()), ("cl", "avg cleanliness", s.cleanliness_rating.mean()),
                   ("ne", "avg nightly equivalent", s.nightly_equivalent_eur.mean())]:
    cmp(name, v, gq[k], g[k])

gc = gold("SELECT city, avg_two_night_total_eur a, median_two_night_total_eur m FROM gold.vw_city_kpis").set_index("city")
dc = data.run("SELECT city, avg(two_night_total_eur) a, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) m FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1", F).set_index("city")
sc = s.groupby("city").two_night_total_eur.agg(["mean", "median"])
for c in sc.index:
    cmp(f"{c} avg two-night total", sc.loc[c, "mean"], gc.loc[c, "a"], dc.loc[c, "a"])
    cmp(f"{c} median two-night total", sc.loc[c, "median"], gc.loc[c, "m"], dc.loc[c, "m"])
rank_s = sc["mean"].sort_values(ascending=False).index.tolist()
rank_g = gc.a.sort_values(ascending=False).index.tolist()
rank_d = dc.a.sort_values(ascending=False).index.tolist()
rank_ok = rank_s == rank_g == rank_d

wp = gold("SELECT city, avg_weekend_diff_pct FROM gold.vw_weekend_premium").set_index("city").avg_weekend_diff_pct
m = s.groupby(["city", "day_type"]).two_night_total_eur.mean().unstack()
dd = data.run("SELECT city, day_type, avg(two_night_total_eur) a FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1,2", F).pivot(index="city", columns="day_type", values="a")
for c in m.index:
    cmp(f"{c} weekend-vs-weekday avg diff %", 100 * (m.loc[c, "weekend"] / m.loc[c, "weekday"] - 1), wp[c], 100 * (dd.loc[c, "weekend"] / dd.loc[c, "weekday"] - 1))

rt = gold("SELECT room_type, avg_two_night_total_eur a, median_two_night_total_eur m FROM gold.vw_room_type_stats").set_index("room_type")
dr = data.run("SELECT room_type, avg(two_night_total_eur) a, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) m FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1", F).set_index("room_type")
for r in rt.index:
    sub = s[s.room_type == r].two_night_total_eur
    cmp(f"{r} avg", sub.mean(), rt.loc[r, "a"], dr.loc[r, "a"])
    cmp(f"{r} median", sub.median(), rt.loc[r, "m"], dr.loc[r, "m"])

df = pd.DataFrame(rows)
bad = df[~df.match]
out = {"tolerance_rel": TOL, "comparisons": len(df), "mismatches": len(bad), "city_ranking_identical": rank_ok,
       "city_ranking_by_avg_price": rank_s, "rows": rows}
(ROOT / "artifacts/reports").mkdir(parents=True, exist_ok=True)
(ROOT / "artifacts/reports/numeric_validation.json").write_text(json.dumps(out, indent=2))
(ROOT / "artifacts/reports/numeric_validation.md").write_text(
    "# Numeric validation: Silver (pandas) vs Gold (SQL) vs dashboard query layer\n\n"
    f"Comparisons: {len(df)} | mismatches: {len(bad)} | relative tolerance {TOL} | city ranking identical across all three: {rank_ok}\n\n"
    + df.to_markdown(index=False, floatfmt=".6f"))
print(f"comparisons={len(df)} mismatches={len(bad)} ranking_identical={rank_ok}")
sys.exit(1 if len(bad) or not rank_ok else 0)
