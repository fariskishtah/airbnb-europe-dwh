# How to run (macOS, Python 3.12, ~1 GB disk, no paid services)
```bash
cd airbnb-europe-sprint1
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
