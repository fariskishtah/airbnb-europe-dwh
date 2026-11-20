"""Central configuration. Credentials come only from the environment (never committed)."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SILVER_DIR = ROOT / "data" / "silver"
MANIFEST_DIR = ROOT / "data" / "manifests"
SOURCE_MANIFEST = ROOT / "data" / "SOURCE_MANIFEST.txt"
DDL_DIR = ROOT / "3_gold_layer" / "ddl"
TRANSFORM_DIR = ROOT / "3_gold_layer" / "transformations"
ANALYTICS_SQL_DIR = ROOT / "3_gold_layer" / "analytics_queries"
REPORT_DIR = ROOT / "artifacts" / "reports"

DEFAULT_URL = "postgresql://127.0.0.1:54329/airbnb_dwh"  # local, loopback-only, trust auth (no password)

SOURCE_DOI = "10.5281/zenodo.4446043"
SOURCE_URL = "https://doi.org/10.5281/zenodo.4446043"
SOURCE_LICENSE = "CC BY 4.0"

# Verbatim CSV header (first column is the unnamed exported row index).
EXPECTED_HEADER = [
    "", "realSum", "room_type", "room_shared", "room_private", "person_capacity",
    "host_is_superhost", "multi", "biz", "cleanliness_rating", "guest_satisfaction_overall",
    "bedrooms", "dist", "metro_dist", "attr_index", "attr_index_norm", "rest_index",
    "rest_index_norm", "lng", "lat",
]
# Bronze column names (lower-case; unnamed index column -> source_row_index)
BRONZE_COLUMNS = ["source_row_index"] + [c.lower() for c in EXPECTED_HEADER[1:]]

FILENAME_RE = re.compile(r"^(?P<city>[a-z]+)_(?P<day>weekdays|weekends)\.csv$")


def database_url(url: str | None = None) -> str:
    """libpq-style URL. Override with AIRBNB_DWH_URL (e.g. for the test database)."""
    return url or os.environ.get("AIRBNB_DWH_URL", DEFAULT_URL)


def sqlalchemy_url(url: str | None = None) -> str:
    u = database_url(url)
    return u.replace("postgresql://", "postgresql+psycopg://", 1) if u.startswith("postgresql://") else u


def zenodo_md5() -> dict[str, str]:
    """Authoritative MD5 per file as recorded in the verified SOURCE_MANIFEST.txt."""
    out: dict[str, str] = {}
    if SOURCE_MANIFEST.exists():
        for line in SOURCE_MANIFEST.read_text().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 6 and parts[0].endswith(".csv"):
                out[parts[0]] = parts[4]
    return out
