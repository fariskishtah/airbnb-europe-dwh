#!/usr/bin/env python
"""Build Airbnb_Europe_DWH_Project_Report.pdf from real project results (JSON artifacts, analytics CSVs, screenshots)."""
import json
import sys
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "artifacts/reports/Airbnb_Europe_DWH_Project_Report.pdf"
GITHUB = sys.argv[2] if len(sys.argv) > 2 else "https://github.com/fariskishtah/airbnb-europe-dwh"
R = ROOT / "artifacts/reports"
A = R / "analytics"
dqr = json.loads((R / "data_quality_report.json").read_text())
nv = json.loads((R / "numeric_validation.json").read_text())
bv = json.loads((R / "browser_verification.json").read_text())
silver_rep = json.loads((ROOT / "data/silver/silver_report.json").read_text())
prof = json.loads((R / "data_profile.json").read_text())["summary"]
testres = json.loads((R / "test_results.json").read_text()) if (R / "test_results.json").exists() else {"passed": "n/a", "failed": "n/a", "skipped": "n/a"}

NAVY = colors.HexColor("#0A1830"); CYAN = colors.HexColor("#0891B2")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], textColor=NAVY, fontSize=17, spaceBefore=6, spaceAfter=8)
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.6, leading=13.5)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8, leading=10.5, textColor=colors.HexColor("#475569"))
n = [0]


def P(t, st=BODY): return Paragraph(t, st)
def table(df, widths=None, fs=7.5):
    data = [list(df.columns)] + df.astype(str).values.tolist()
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), fs),
                           ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#CBD5E1")), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t
def img(path, w=16.5 * cm):
    from PIL import Image as PI
    iw, ih = PI.open(path).size
    return Image(str(path), width=w, height=w * ih / iw)
def sec(title): n[0] += 1; return Paragraph(f"{n[0]}. {title}", H1)
def csv(name): return pd.read_csv(A / f"{name}.csv")


def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.grey)
    c.drawString(2 * cm, 1.1 * cm, "Airbnb Europe Analytics - Sprint 1 - Faris Mohamed Kishtah"); c.drawRightString(19 * cm, 1.1 * cm, f"Page {d.page}"); c.restoreState()


def cover(c, d):
    c.setFillColor(NAVY); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#22D3EE")); c.rect(2 * cm, 17.4 * cm, 3 * cm, .25 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 34); c.drawString(2 * cm, 15.6 * cm, "Airbnb Europe Analytics")
    c.setFont("Helvetica", 17); c.drawString(2 * cm, 14.4 * cm, "End-to-End Medallion Data Warehouse")
    c.setFillColor(colors.HexColor("#9FB6D8")); c.setFont("Helvetica", 12)
    for i, t in enumerate(["INSTANT AI & Data Science Training", "Sprint 1 - Data Analysis", "Official project: Airbnb Prices in European Cities", "",
                           "Prepared by: Faris Mohamed Kishtah", "Built: 2026-11-20", "",
                           "Power BI (.pbix) NOT included - replaced by a SQL-connected Streamlit + Plotly dashboard"]):
        c.drawString(2 * cm, (12.4 - i * .7) * cm, t)


story = []
story += [Spacer(1, 1), PageBreak()]
top = csv("01_price_by_city"); wk = csv("02_weekday_vs_weekend"); rm = csv("03_price_by_room_type"); sh = csv("04_price_by_superhost")
corr = csv("07_correlations").iloc[0]; dist = csv("09_price_distribution").iloc[0]
passed = dqr["passed"]; total = passed + dqr["failed"]

story += [sec("Executive Summary"),
 P(f"This project delivers a reproducible Bronze-Silver-Gold data warehouse for the Zenodo dataset <i>Airbnb Prices in European Cities</i> "
   f"(DOI 10.5281/zenodo.4446043, CC BY 4.0): <b>{prof['files']} files, {prof['rows']:,} offer observations, {prof['cities']} cities</b>. Raw files were verified against Zenodo MD5 checksums, loaded unchanged to PostgreSQL (Bronze), "
   f"validated and typed (Silver, {silver_rep['rows_quarantined']} rows quarantined, 0 imputed) and modelled as a star schema (Gold: 5 dimensions + 1 fact). "
   f"A Streamlit + Plotly dashboard with 8 pages reads live from the SQL warehouse. {passed}/{total} automated data-quality checks pass; the automated test suite reports {testres['passed']} passed, {testres['failed']} failed, {testres['skipped']} skipped."),
 P("<b>Important deviation:</b> the assignment requests a Power BI .pbix report. <b>No .pbix is included</b>; the Streamlit dashboard is a functional alternative and the original requirement is not satisfied."),
 sec("Project Objective"),
 P("Complete Sprint 1 end to end: ingest all CSV files (Bronze), detect nulls, clean, assess enrichment and combine into a master dataset (Silver), import into SQL and build a dimensional model (Gold), and provide a business-intelligence dashboard. The original suggested dimensions are City, Property Type, Room Type, Host and Date; only those the data supports were built."),
 sec("Dataset Description"),
 P(f"Each city has a weekday and a weekend file with the same 20 columns (one unnamed exported row index + 19 analytical). Key fields: <b>realSum</b> (price for two people and two nights, EUR), room type, capacity, superhost/multi/biz host flags, cleanliness (0-10), guest satisfaction (0-100), bedrooms, distance to centre and metro (km), attraction and restaurant indices, longitude/latitude. "
   f"Blank cells: {prof['blank_cells']}; exact duplicate rows: {prof['exact_duplicate_rows_excluding_index']}. There is <b>no calendar date, no listing id, no host id and no property type</b>."),
 sec("Data Source and Provenance"),
 P("Source: Gyodi and Nawaro, <i>Determinants of Airbnb prices in European cities</i> (supplementary material), Zenodo v2, 2021-01-13, https://doi.org/10.5281/zenodo.4446043, licence CC BY 4.0. Files were downloaded from the Zenodo record API; all 20 MD5 sums match the record. A Kaggle repack was found byte-identical earlier in the project and is not used."),
 PageBreak(), sec("Bronze Layer"),
 P("Pipeline: validate sources (existence, identical header, MD5 vs Zenodo, no duplicate content) -> manifest (filename, city, day type, rows, columns, size, SHA-256, MD5, timestamp) -> idempotent load of every value as text into <font face='Courier'>bronze.raw_offers</font> with source file and row number. Re-running skips unchanged files (verified: 0 loaded / 20 skipped) and rejects the same content under another name. Raw CSVs are never modified."),
 sec("Data Profiling"),
 P(f"Price is strongly right-skewed: median EUR {dist['p50']}, mean EUR {dist['mean']}, 99th percentile EUR {dist['p99']}, maximum EUR {dist['max']:,.0f} ({prof['price_outliers_gt_5000']} offers above EUR 5,000). Cleanliness and satisfaction show ceiling effects. multi and biz are never both 1. Full report: docs/DATA_PROFILING.md."),
 sec("Silver Layer"),
 P("Silver reads the raw text, applies strict typing and 12 validation rules (non-null, positive price, room-type domain, room-flag consistency, rating ranges, capacity, bedrooms, distances, indices, binary flags, coordinates near the city). Rows failing any rule would be quarantined rather than dropped or repaired."),
 sec("Data Cleaning"),
 P(f"Because the source is clean, the genuine result is: {silver_rep['rows_in']:,} rows in, {silver_rep['rows_out']:,} out, {silver_rep['rows_quarantined']} quarantined, 0 imputed values, {silver_rep['duplicate_offer_ids']} duplicate keys. No artificial cleaning was added. Derived columns: offer_id, two_night_total_eur (= realSum), nightly_equivalent_eur (= realSum / 2, a derived equivalent - not an observed nightly rate, not per person), is_studio, price_outlier_iqr ({silver_rep['price_outliers_flagged']:,} offers above the per-city/day-type upper Tukey fence; flagged, not removed)."),
 sec("Master Dataset"),
 P("data/silver/airbnb_europe_master.parquet and .csv, table silver.airbnb_europe_master. Reconciliation: Bronze 51,707 = Silver 51,707 = Gold 51,707; every Silver row traces to a Bronze row (source_file + source_row_index); real_sum equals Bronze realSum with no drift."),
 PageBreak(), sec("Gold Layer"),
 P("PostgreSQL 16.2. The gold schema is rebuilt from Silver by SQL scripts (3_gold_layer/ddl, transformations) with deterministic surrogate keys, 6 primary keys, 7 foreign keys, a unique grain constraint, CHECK constraints, indexes and analytical views."),
 sec("Star Schema"), img(ROOT / "artifacts/figures/star_schema.png", 14 * cm),
 P("Grain: one offer observation = one row of one source CSV. <b>Not built:</b> Date (no date in source), Host (no host id; only portfolio flags in dim_host_status), Property Type (not in source).", SMALL),
 PageBreak(), sec("SQL Implementation"),
 P("Analytical SQL lives in 3_gold_layer/analytics_queries (12 queries) over views vw_offers_enriched, vw_city_kpis, vw_weekend_premium, vw_room_type_stats, vw_superhost_stats, vw_capacity_stats, vw_layer_reconciliation. Medians use percentile_cont because prices are skewed."),
 img(ROOT / "artifacts/figures/architecture.png", 8 * cm),
 PageBreak(), sec("Data Quality")]
dq = pd.DataFrame(dqr["checks"])[["layer", "name", "expected", "actual", "status"]]
dq["name"] = dq["name"].str.slice(0, 58)
story += [P(f"{passed}/{total} checks pass (computed, not hard-coded): file presence, MD5, rows per file, Bronze to Silver to Gold reconciliation, price-sum reconciliation, lineage, value ranges, referential integrity, grain uniqueness, constraint counts."),
          table(dq, [1.5 * cm, 8.3 * cm, 2.7 * cm, 2.7 * cm, 1.3 * cm], 6.8), PageBreak(), sec("Analytical KPIs")]
t1 = top.copy(); story += [P("Two-night total (2 guests, 2 nights, EUR) by city; median reported because of skew."), table(t1, None, 8), Spacer(1, 6),
          P("Room type:"), table(rm, None, 8), Spacer(1, 6), P("Superhost status (association only; superhosts differ by city and room mix):"), table(sh, None, 8),
          sec("Dashboard Architecture"),
          P("Streamlit multipage app (4_web_dashboard): components/data.py (read-only SQLAlchemy engine, parameterised queries, cache), components/filters.py (global filters rewrite the SQL WHERE clause with bound parameters), eight pages, queries/catalog.py (whitelisted metrics and groupings for the SQL Explorer, no free-form SQL). Plotly charts with a navy/cyan theme; CSV export on every table."),
          img(ROOT / "artifacts/figures/data_lineage.png", 15 * cm), PageBreak(), sec("Dashboard Screenshots"),
          P("Genuine Playwright/Chromium screenshots captured from the running application.", SMALL)]
for s in ["01_executive_overview", "02_city_intelligence", "03_pricing_analytics", "04_property_room", "05_ratings_location", "06_geospatial", "07_data_quality_pipeline", "08_sql_explorer"]:
    story += [img(ROOT / f"artifacts/screenshots/{s}.png", 13.5 * cm), P(s.replace("_", " "), SMALL), Spacer(1, 4)]
story += [PageBreak(), sec("Key Findings"),
 P(f"All findings are descriptive; the data are observational. (1) Average two-night total is highest in {top.city.iloc[0]} (EUR {top.avg_eur.iloc[0]}) and lowest in {top.city.iloc[-1]} (EUR {top.avg_eur.iloc[-1]}). "
   f"(2) Entire homes average EUR {rm.avg_eur.iloc[0]}, private rooms EUR {rm.avg_eur.iloc[1]}, shared rooms EUR {rm.avg_eur.iloc[2]}. "
   f"(3) Weekend vs weekday average difference ranges from {wk.avg_diff_pct.max():+.1f}% ({wk.city.iloc[0]}) to {wk.avg_diff_pct.min():+.1f}% ({wk.city.iloc[-1]}); these are different samples, not the same listings. "
   f"(4) Correlations with price: attraction index {corr.price_vs_attraction_idx}, bedrooms {corr.price_vs_bedrooms}, capacity {corr.price_vs_capacity}, distance to centre {corr.price_vs_dist_center}, satisfaction {corr.price_vs_satisfaction}, cleanliness {corr.price_vs_cleanliness}. Correlation does not establish causation."),
 P("Weekday vs weekend by city:"), table(wk, None, 7.5),
 sec("Technical Challenges"),
 P("(a) Homebrew PostgreSQL 14 was broken (missing ICU library) and Docker was not running; solved by a venv-bundled PostgreSQL 16 (pgserver) managed by other_scripts/pg_local.sh. (b) Pandas/Streamlit API differences found by browser testing (a failing page was caught only by the real-browser run and fixed). (c) The map initially opened on Africa; centre and zoom are now computed from the data. (d) A data-quality check expected 10 foreign keys; the real design has 7 - the expectation was corrected, not the schema."),
 sec("Testing"),
 P(f"pytest: <b>{testres['passed']} passed, {testres['failed']} failed, {testres['skipped']} skipped</b> - Bronze (discovery, manifest, raw preservation, idempotency, duplicate rejection), Silver (schema, cleaning, quarantine, lineage, determinism), Gold (PK/FK, grain, reconciliation, aggregates vs pandas, stable keys), Dashboard (KPIs, filters, empty results, invalid inputs, every page via Streamlit AppTest), Security (SQL injection, read-only session, unsafe paths, secret scan). Integration tests rebuild the whole pipeline in a separate PostgreSQL database."),
 P(f"Numeric validation: {nv['comparisons']} KPI comparisons between Silver (pandas), Gold (SQL) and the dashboard query layer, {nv['mismatches']} mismatches (relative tolerance 1e-9), identical city ranking: {nv['city_ranking_identical']}. "
   f"Browser verification (Playwright): {len([p for p in bv['pages'] if p['viewport']=='desktop'])} desktop pages and {len([p for p in bv['pages'] if p['viewport']=='mobile'])} mobile pages, {sum(p['exceptions'] for p in bv['pages'])} Streamlit exceptions, {len(bv['console_errors'])} browser console errors. A Paris filter test changed the KPI from 51,707 to 6,688 observations (matches SQL) and a CSV download succeeded."),
 sec("Reproducibility"),
 P("make setup db-start; make all; make dashboard. All steps idempotent; Makefile and HOW_TO_RUN.md document each command; dependencies pinned in requirements.txt."),
 sec("Limitations"),
 P("No calendar date (no time series, seasonality, booking lead time); no listing or host id (no listing-level analysis, repeated listings undetectable); price is a two-night two-guest total; coordinates are perturbed; dataset is a 2020-era snapshot; weekday/weekend are separate samples; external enrichment/scraping was deliberately not performed (no reliable join key, ToS and legal constraints, temporal mismatch)."),
 sec("Power BI Substitution"),
 P("<b>The original assignment requests a Power BI .pbix report. This submission instead provides a working SQL-connected Streamlit + Plotly dashboard. No .pbix file is included.</b> No DAX measures, Power BI themes or .pbix artefacts exist. The Streamlit dashboard offers equivalent interactive analytics over the same SQL model but does not satisfy the exact deliverable."),
 sec("Conclusion"),
 P("The warehouse, star schema, quality framework, tests and dashboard are technically complete and verified. Exact compliance with the original assignment is partial: Power BI .pbix, Date/Host/Property dimensions (unsupported by the data) and external enrichment (deliberately skipped) are not delivered."),
 sec("GitHub Repository"), P(f"{GITHUB}"), P("LinkedIn: PENDING &nbsp;&nbsp; Facebook: PENDING")]

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title="Airbnb Europe Analytics - End-to-End Medallion Data Warehouse", author="Faris Mohamed Kishtah")
doc.build(story, onFirstPage=cover, onLaterPages=footer)
print("PDF:", OUT)
