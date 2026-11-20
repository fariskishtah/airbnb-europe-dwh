PY ?= .venv/bin/python
.PHONY: setup db-start db-stop validate bronze profile silver gold quality analytics validate-numbers test dashboard browser-verify all
setup:            ## create venv and install dependencies
	python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
db-start:         ## start local PostgreSQL (venv-bundled) and create databases
	other_scripts/pg_local.sh init && other_scripts/pg_local.sh start && other_scripts/pg_local.sh createdb airbnb_dwh && other_scripts/pg_local.sh createdb airbnb_dwh_test
db-stop:
	other_scripts/pg_local.sh stop
validate:         ## 1. validate 20 source CSVs (existence, schema, MD5 vs Zenodo)
	$(PY) 1_bronze_layer/validation/validate_sources.py
bronze: validate  ## 2. Bronze ingestion (idempotent)
	$(PY) 1_bronze_layer/ingestion/run_bronze.py
profile:
	$(PY) 1_bronze_layer/validation/profile_data.py
silver:           ## 3. Silver master dataset + load to PostgreSQL
	$(PY) 2_silver_layer/transformation/run_silver.py
gold:             ## 4. Gold star schema (rebuilt from Silver)
	$(PY) 3_gold_layer/transformations/run_gold.py
quality:          ## 5. automated data-quality checks
	$(PY) 3_gold_layer/quality_checks/run_quality_checks.py
analytics:        ## 6. run analytical SQL -> artifacts/reports/analytics
	$(PY) 3_gold_layer/analytics_queries/run_analytics.py
validate-numbers:
	$(PY) other_scripts/validate_numbers.py
test:
	$(PY) -m pytest -q
dashboard:        ## 7. launch Streamlit dashboard on http://localhost:8501
	.venv/bin/streamlit run 4_web_dashboard/app.py
browser-verify:   ## needs the dashboard running on :8599 (see HOW_TO_RUN.md)
	$(PY) other_scripts/browser_verify.py http://localhost:8599
all: bronze profile silver gold quality analytics validate-numbers test
