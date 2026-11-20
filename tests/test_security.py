import re
import subprocess
from pathlib import Path

import pytest
import sqlalchemy

from airbnb_dwh import bronze, config
from components import data
from test_dashboard import full_filters

ROOT = Path(__file__).resolve().parents[1]


def test_sql_injection_in_filter_values_is_inert(warehouse):
    evil = "x'; DROP TABLE gold.fact_offer_observation; --"
    f = full_filters(warehouse, cities=[evil, "Paris"], room_types=["Private room' OR '1'='1"])
    assert data.run("SELECT count(*) n FROM gold.vw_offers_enriched WHERE {WHERE}", f)["n"][0] == 0
    assert warehouse.execute("SELECT count(*) FROM gold.fact_offer_observation").fetchone()[0] == 51707


def test_dashboard_connection_is_read_only(warehouse):
    eng = data.get_engine()
    with eng.connect() as c, pytest.raises(sqlalchemy.exc.DBAPIError):
        c.execute(sqlalchemy.text("DELETE FROM gold.dim_city"))


def test_unsafe_raw_paths_rejected():
    for bad in ["../../etc/passwd", "../silver/airbnb_europe_master.csv", "/etc/passwd", "rome_weekdays.csv.exe", "a/b_weekdays.csv"]:
        with pytest.raises(ValueError):
            bronze.safe_raw_path(bad)
    assert bronze.safe_raw_path("rome_weekdays.csv").name == "rome_weekdays.csv"


def test_no_credentials_in_default_config():
    assert "@" not in config.DEFAULT_URL and "password" not in config.DEFAULT_URL.lower()


def test_no_secrets_in_source_tree():
    pat = re.compile(r"(password\s*=\s*['\"][^'\"]+['\"]|postgres(?:ql)?(?:\+\w+)?://\w+:[^@\s]+@|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})")
    hits = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".sql", ".md", ".toml", ".txt", ".sh", ".example", ".yml", ".yaml", ".json"} \
                and not any(x in p.parts for x in (".venv", ".pgdata", "__pycache__", ".git")) and "tests" not in p.parts:
            if pat.search(p.read_text(errors="ignore")):
                hits.append(str(p))
    assert not hits, hits
