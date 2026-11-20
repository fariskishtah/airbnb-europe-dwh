# Gold layer
`ddl/` (00 reference, 01 bronze/silver tables, 02 star schema, 03 views) · `transformations/` (10 load dims + fact, `run_gold.py`) · `quality_checks/run_quality_checks.py` (29 checks → `meta.dq_result` + `artifacts/reports/data_quality_report.json`) · `analytics_queries/` (12 SQL files + runner → `artifacts/reports/analytics/*.csv`).
