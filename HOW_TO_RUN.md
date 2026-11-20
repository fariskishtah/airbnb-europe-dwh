# How to run (macOS, Python 3.12, ~1 GB disk, no paid services)
```bash
cd airbnb-europe-sprint1      # in the submission ZIP this folder is 02_PROJECT_FILES/
make setup            # python3.12 -m venv .venv && pip install -r requirements.txt
make db-start         # init + start PostgreSQL 16 (venv-bundled) on 127.0.0.1:54329, create airbnb_dwh and airbnb_dwh_test
make validate         # 20 files, schema, MD5 vs Zenodo
make bronze silver gold quality analytics validate-numbers
make test             # 52 tests (uses the airbnb_dwh_test database)
make dashboard        # http://localhost:8501
```
Or all at once: `make all`. Stop the database: `make db-stop`. Use another PostgreSQL by exporting `AIRBNB_DWH_URL=postgresql://host:port/db`.
Raw data are already in `data/raw/`; if missing, download the 20 CSVs from https://doi.org/10.5281/zenodo.4446043 (record 4446043) into `data/raw/` and `make validate` will verify them against `data/SOURCE_MANIFEST.txt`.
Browser verification: start the dashboard on port 8599 (`.venv/bin/streamlit run 4_web_dashboard/app.py --server.port 8599`), `.venv/bin/playwright install chromium`, then `make browser-verify` and `.venv/bin/python other_scripts/browser_interactions.py`.

## Clean-environment notes
- Requirements: macOS/Linux, Python 3.12 (`python3.12` on PATH), internet access for `pip install`. Nothing else: PostgreSQL 16 comes from the pip package `pgserver`; no Docker, no system PostgreSQL.
- `make setup` creates `.venv`; `make db-start` creates a fresh cluster in `.pgdata/` (trust auth, loopback only, no password) and the two databases. `make all` then regenerates Bronze, Silver (parquet/csv), Gold, quality reports, analytics, numeric validation and the tests from the raw CSVs. No pre-existing database or generated file is required.
- Optional environment variables (all have working defaults): `AIRBNB_DWH_URL` (database for pipeline and dashboard), `AIRBNB_DWH_TEST_URL` (database used by pytest; it is rebuilt by the tests, so never point it at real data), `AWH_PGPORT` (default 54329), `AWH_PGDATA` (default `.pgdata`), `AWH_PGSOCK` (default `/tmp/awh_pg`).
- If port 54329 is busy, e.g. `AWH_PGPORT=54330 AIRBNB_DWH_URL=postgresql://127.0.0.1:54330/airbnb_dwh AIRBNB_DWH_TEST_URL=postgresql://127.0.0.1:54330/airbnb_dwh_test make db-start all`.
