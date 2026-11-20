# Project status (generated 2026-11-20)
| Area | Status | Verified by |
|---|---|---|
| Source files (20 CSV, 51,707 rows) | verified | MD5 vs Zenodo 20/20 |
| Bronze | complete | manifest + 51,707 raw rows, idempotent re-run (0 loaded / 20 skipped) |
| Silver | complete | 51,707 rows, 0 quarantined, 0 imputed |
| Gold star schema | complete | 5 dims + fact, FK/PK verified in catalog |
| Data quality | 29/29 pass | `artifacts/reports/data_quality_report.json` |
| Tests | 52 passed / 0 failed / 0 skipped | `pytest` |
| Numeric validation | 42 comparisons, 0 mismatches | `artifacts/reports/numeric_validation.md` |
| Dashboard | 8 pages working | Playwright: 0 exceptions, 0 console errors |
| Power BI `.pbix` | **not implemented** | disclosed |
Known gaps: no Date/Host/Property dimensions (data limits), no external enrichment (by design), LinkedIn/Facebook PENDING.
