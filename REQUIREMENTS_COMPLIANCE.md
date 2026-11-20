# Requirements compliance (Sprint 1 – Airbnb Prices in European Cities)

Status legend: IMPLEMENTED · PARTIALLY IMPLEMENTED · NOT IMPLEMENTED · REPLACED WITH ALTERNATIVE

| # | Official requirement | Status | Evidence / note |
|---|---|---|---|
| B1 | Bronze: load all CSV files | IMPLEMENTED | 20/20 files, 51,707 rows in `bronze.raw_offers`; `1_bronze_layer/ingestion/run_bronze.py` |
| B2 | Understand common columns | IMPLEMENTED | identical 20-column header in all files; `docs/DATA_PROFILING.md`, `DATA_DICTIONARY.md` |
| B3 | Preserve raw values / store raw staging | IMPLEMENTED | text-exact copy (test `test_bronze_preserves_raw_values_exactly`), manifest with SHA-256 |
| S1 | Silver: detect null values | IMPLEMENTED | 0 nulls found; detection logic runs and reports (`silver_report.json`) – no cleaning was invented |
| S2 | Identify missing/useful external features; permitted enrichment | PARTIALLY IMPLEMENTED | assessed and **deliberately not performed** (no join key, ToS/legal, temporal mismatch): `docs/ENRICHMENT_DECISION.md`. No scraping done. |
| S3 | Clean and enrich | IMPLEMENTED | typing, 12 validation rules + quarantine, derived metrics (`nightly_equivalent_eur`, `is_studio`, outlier flag) |
| S4 | Combine files into master dataset | IMPLEMENTED | `data/silver/airbnb_europe_master.{parquet,csv}`, 51,707 rows, reconciled to Bronze |
| G1 | Import cleaned data into SQL | IMPLEMENTED | PostgreSQL 16, `silver.airbnb_europe_master` |
| G2 | Dimensional model: fact + dimensions, PK/FK, relationships | IMPLEMENTED | 5 dims + 1 fact, 6 PKs, 7 FKs, unique grain constraint, indexes, views |
| G3 | Dimension City | IMPLEMENTED | `dim_city` |
| G4 | Dimension Room Type | IMPLEMENTED | `dim_room_type` |
| G5 | Dimension **Property Type** | NOT IMPLEMENTED | source has no property-type field (only room type); fabricating it is not acceptable |
| G6 | Dimension **Host** | REPLACED WITH ALTERNATIVE | no host id exists; `dim_host_status` holds superhost/multi/biz flags only (no individual hosts) |
| G7 | Dimension **Date** | NOT IMPLEMENTED | source has no calendar date; `dim_day_type` (weekday/weekend sample) is the only temporal attribute |
| D1 | **Power BI `.pbix` report** | **NOT IMPLEMENTED** | *The original assignment requests a Power BI .pbix report. This submission instead provides a working SQL-connected Streamlit + Plotly dashboard. No .pbix file is included.* |
| D2 | Interactive BI dashboard over the warehouse | REPLACED WITH ALTERNATIVE | Streamlit + Plotly, 8 pages, SQL-backed, global filters, exports, browser-verified. Useful as a functional alternative, **not** the requested deliverable. |
| F1 | End-to-end Data Warehouse project (not only notebooks) | IMPLEMENTED | scripts, SQL DDL, Makefile, 52 tests, docs, PDF report |
| F2 | Professional repository | IMPLEMENTED | https://github.com/fariskishtah/airbnb-europe-dwh |
| F3 | Social posts (LinkedIn / Facebook) | NOT IMPLEMENTED | PENDING – to be handled separately; no URLs invented |

**Technical completion vs exact compliance:** the data-warehouse, star-schema and dashboard work are technically complete and verified; exact compliance with the original assignment is **PARTIAL** because of D1 (no `.pbix`), G5/G7 (impossible from the data) and S2 (no enrichment by design).
