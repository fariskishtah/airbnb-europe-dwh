#!/usr/bin/env python
"""Draw architecture / star-schema / pipeline / lineage diagrams. The star schema is read from the live database catalog."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from airbnb_dwh import db  # noqa: E402

OUT = ROOT / "artifacts/figures"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, CYAN, BLUE, AMBER, GREEN, GREY = "#0A1830", "#22D3EE", "#3B82F6", "#F59E0B", "#34D399", "#94A3B8"


def box(ax, x, y, w, h, text, fc, tc="white", fs=10, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec="white", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, p1, p2, color="white"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=16, color=color, lw=1.8))


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=NAVY)
    ax.set_facecolor(NAVY); ax.axis("off"); ax.set_xlim(0, w); ax.set_ylim(0, h)
    ax.text(w / 2, h - 0.35, title, ha="center", color="white", fontsize=15, fontweight="bold")
    return fig, ax


# 1. architecture
steps = [("RAW CSV FILES\n20 files · 51,707 rows\nZenodo 4446043", GREY), ("BRONZE LAYER\nraw text in PostgreSQL\n+ manifest, SHA-256", AMBER),
         ("DATA PROFILING\nnulls, ranges, outliers", GREY), ("SILVER LAYER\ntyped, validated,\nlineage kept", BLUE),
         ("CLEAN MASTER DATASET\nparquet + csv + silver.*", BLUE), ("GOLD SQL WAREHOUSE\nPostgreSQL 16", CYAN),
         ("STAR SCHEMA\n5 dims + 1 fact", CYAN), ("SQL ANALYTICS\nviews + 12 queries", GREEN), ("STREAMLIT DASHBOARD\n8 pages · Plotly", GREEN)]
fig, ax = canvas(7, 13.2, "Architecture: Airbnb Europe Medallion Data Warehouse")
for i, (t, c) in enumerate(steps):
    y = 11.7 - i * 1.3
    box(ax, 1.5, y, 4, 0.95, t, c, tc="black" if c in (CYAN, GREEN, AMBER, GREY) else "white", fs=10)
    if i < len(steps) - 1:
        arrow(ax, (3.5, y), (3.5, y - 0.33))
fig.savefig(OUT / "architecture.png", dpi=170, facecolor=NAVY, bbox_inches="tight"); plt.close(fig)

# 2. star schema from catalog
with db.connect() as conn:
    cols = conn.execute("""SELECT c.table_name, c.column_name, c.data_type FROM information_schema.columns c
        WHERE c.table_schema='gold' AND c.table_name IN ('dim_city','dim_day_type','dim_room_type','dim_host_status','dim_source_file','fact_offer_observation')
        ORDER BY c.table_name, c.ordinal_position""").fetchall()
    pks = {(r[0], r[1]) for r in conn.execute("""SELECT cl.relname, a.attname FROM pg_constraint c JOIN pg_class cl ON cl.oid=c.conrelid
        JOIN pg_attribute a ON a.attrelid=cl.oid AND a.attnum=ANY(c.conkey) JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='gold' AND c.contype='p'""")}
    fks = {(r[0], r[1]) for r in conn.execute("""SELECT cl.relname, a.attname FROM pg_constraint c JOIN pg_class cl ON cl.oid=c.conrelid
        JOIN pg_attribute a ON a.attrelid=cl.oid AND a.attnum=ANY(c.conkey) JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='gold' AND c.contype='f'""")}
tables: dict = {}
for t, c, d in cols:
    tables.setdefault(t, []).append(c)
fig, ax = canvas(15, 11, "Gold star schema (read from the live PostgreSQL catalog)")
pos = {"dim_city": (0.3, 7.3), "dim_day_type": (5.7, 8.3), "dim_room_type": (10.4, 7.3), "dim_host_status": (0.3, 1.0),
       "dim_source_file": (10.4, 1.0), "fact_offer_observation": (5.4, 1.2)}
centres = {}
for t, (x, y) in pos.items():
    cs = tables[t]; h = 0.34 * (len(cs) + 1); w = 4.3 if t == "fact_offer_observation" else 4.2
    if t == "fact_offer_observation":
        h = 0.27 * (len(cs) + 1) + 0.35
    top = y + h if t != "fact_offer_observation" else y + h
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#11284B", ec=CYAN if t.startswith("fact") else BLUE, lw=2))
    ax.text(x + w / 2, y + h - 0.25, t, ha="center", color=CYAN if t.startswith("fact") else "white", fontsize=11, fontweight="bold")
    step = 0.27 if t == "fact_offer_observation" else 0.34
    for i, c in enumerate(cs):
        tag = "PK " if (t, c) in pks else ("FK " if (t, c) in fks else "   ")
        ax.text(x + 0.15, y + h - 0.6 - i * step, f"{tag}{c}", color=AMBER if tag.strip() == "PK" else (GREEN if tag.strip() == "FK" else "#C8D9F2"), fontsize=7.6, family="monospace")
    centres[t] = (x + w / 2, y + h / 2, x, y, w, h)
f = centres["fact_offer_observation"]
for d in ["dim_city", "dim_day_type", "dim_room_type", "dim_host_status", "dim_source_file"]:
    c = centres[d]
    arrow(ax, (c[0], c[1] - (c[5] / 2 if c[1] > f[1] else -c[5] / 2)), (f[0] + (c[0] - f[0]) * 0.35, f[1] + (f[5] / 2 if c[1] > f[1] else -f[5] / 2)), GREEN)
c = centres["dim_source_file"]
ax.text(7.5, 0.35, "dim_source_file.city_key -> dim_city and day_type_key -> dim_day_type are also FKs", color=GREY, ha="center", fontsize=9)
fig.savefig(OUT / "star_schema.png", dpi=170, facecolor=NAVY, bbox_inches="tight"); plt.close(fig)

# 3. pipeline execution
fig, ax = canvas(15, 5, "Pipeline execution (make targets)")
seq = [("make validate\nMD5 · schema", GREY), ("make bronze\nraw text → bronze.*", AMBER), ("make silver\nclean → silver.*", BLUE), ("make gold\nstar schema", CYAN),
       ("make quality\n29 checks", GREEN), ("make analytics\nSQL results", GREEN), ("make dashboard\nStreamlit", GREEN)]
for i, (t, c) in enumerate(seq):
    x = 0.3 + i * 2.1
    box(ax, x, 1.7, 1.8, 1.5, t, c, tc="black" if c != BLUE else "white", fs=9)
    if i < len(seq) - 1:
        arrow(ax, (x + 1.8, 2.45), (x + 2.1, 2.45))
ax.text(7.5, 0.9, "each step is idempotent · every run recorded in meta.pipeline_run / meta.dq_result", color=GREY, ha="center", fontsize=10)
fig.savefig(OUT / "pipeline_execution.png", dpi=170, facecolor=NAVY, bbox_inches="tight"); plt.close(fig)

# 4. lineage
fig, ax = canvas(15, 6, "Data lineage: row-level traceability")
nodes = [("data/raw/*.csv\n(unchanged)", GREY, 0.3), ("bronze.raw_offers\nsource_file +\nsource_row_number", AMBER, 3.2), ("silver.airbnb_europe_master\noffer_id = city_daytype_row\nsource_file + source_row_index", BLUE, 6.1),
         ("gold.fact_offer_observation\noffer_key · FK to 5 dims", CYAN, 9.3), ("vw_* views → dashboard\n+ analytics_queries", GREEN, 12.3)]
for t, c, x in nodes:
    box(ax, x, 2.2, 2.5 if x < 12 else 2.4, 1.6, t, c, tc="black" if c != BLUE else "white", fs=8.5)
for a, b in [(2.8, 3.2), (5.7, 6.1), (8.6, 9.3), (11.8, 12.3)]:
    arrow(ax, (a, 3.0), (b, 3.0))
ax.text(7.5, 1.3, "51,707 → 51,707 → 51,707 → 51,707 rows · 0 quarantined · 0 imputed", color="white", ha="center", fontsize=11, fontweight="bold")
fig.savefig(OUT / "data_lineage.png", dpi=170, facecolor=NAVY, bbox_inches="tight"); plt.close(fig)
print("diagrams written to", OUT)
