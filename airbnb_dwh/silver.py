"""Silver layer: typed, validated, lineage-preserving master dataset built from the raw CSV files."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import bronze, config
from .reference import CITY_REFERENCE, MAX_COORD_OFFSET_DEG

NUMERIC_SOURCE = ["realSum", "cleanliness_rating", "guest_satisfaction_overall", "dist", "metro_dist",
                  "attr_index", "attr_index_norm", "rest_index", "rest_index_norm", "lng", "lat"]
BOOL_SOURCE = ["room_shared", "room_private", "host_is_superhost"]
VALID_ROOM_TYPES = {"Entire home/apt", "Private room", "Shared room"}

SILVER_COLUMNS = [
    "offer_id", "source_file", "source_row_index", "city", "day_type", "real_sum", "two_night_total_eur",
    "nightly_equivalent_eur", "room_type", "room_shared", "room_private", "person_capacity", "host_is_superhost",
    "multi_listing_host", "business_host", "cleanliness_rating", "guest_satisfaction_overall", "bedrooms",
    "dist_city_center_km", "dist_metro_km", "attr_index", "attr_index_norm", "rest_index", "rest_index_norm",
    "lng", "lat", "is_studio", "price_outlier_iqr",
]


def _strict_bool(s: pd.Series, col: str) -> pd.Series:
    bad = ~s.isin(["True", "False"])
    if bad.any():
        raise ValueError(f"{col}: unexpected boolean literals {s[bad].unique()[:5]}")
    return s.eq("True")


def read_raw(raw_dir: Path | None = None) -> pd.DataFrame:
    """Read every raw CSV as text (no inference) and attach lineage columns."""
    frames = []
    for p in bronze.discover(raw_dir):
        m = config.FILENAME_RE.match(p.name)
        df = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
        df = df.rename(columns={df.columns[0]: "source_row_index"})
        df["source_file"] = p.name
        df["city"] = m["city"]
        df["day_type"] = "weekday" if m["day"] == "weekdays" else "weekend"
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (clean, quarantine, report). Invalid rows are quarantined, never silently dropped or imputed."""
    df = raw.copy()
    report: dict = {"rows_in": int(len(df)), "null_or_blank_cells": int((df.replace("", np.nan).isna()).sum().sum())}
    for c in NUMERIC_SOURCE + ["person_capacity", "bedrooms", "multi", "biz", "source_row_index"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in BOOL_SOURCE:
        df[c] = _strict_bool(df[c], c)
    df["room_type"] = df["room_type"].str.strip()

    ref_lat = df["city"].map({k: v[2] for k, v in CITY_REFERENCE.items()})
    ref_lng = df["city"].map({k: v[3] for k, v in CITY_REFERENCE.items()})
    checks = {
        "numeric_not_null": df[NUMERIC_SOURCE + ["person_capacity", "bedrooms", "multi", "biz"]].notna().all(axis=1),
        "price_positive": df["realSum"] > 0,
        "room_type_valid": df["room_type"].isin(VALID_ROOM_TYPES),
        "room_flags_consistent": (df["room_shared"] == df["room_type"].eq("Shared room"))
                                 & (df["room_private"] == df["room_type"].eq("Private room")),
        "satisfaction_0_100": df["guest_satisfaction_overall"].between(0, 100),
        "cleanliness_0_10": df["cleanliness_rating"].between(0, 10),
        "capacity_ge_1": df["person_capacity"] >= 1,
        "bedrooms_ge_0": df["bedrooms"] >= 0,
        "distances_ge_0": (df["dist"] >= 0) & (df["metro_dist"] >= 0),
        "indices_positive": (df[["attr_index", "attr_index_norm", "rest_index", "rest_index_norm"]] > 0).all(axis=1),
        "flags_binary": df["multi"].isin([0, 1]) & df["biz"].isin([0, 1]),
        "coords_valid": df["lat"].between(-90, 90) & df["lng"].between(-180, 180)
                        & ((df["lat"] - ref_lat).abs() <= MAX_COORD_OFFSET_DEG)
                        & ((df["lng"] - ref_lng).abs() <= MAX_COORD_OFFSET_DEG),
    }
    ok = pd.concat(checks, axis=1)
    report["rule_failures"] = {k: int((~v).sum()) for k, v in ok.items()}
    valid = ok.all(axis=1)
    quarantine = raw.loc[~valid].copy()
    bad = ok.loc[~valid]
    quarantine["failed_rules"] = [",".join(bad.columns[~row]) for row in bad.to_numpy()] if len(bad) else pd.Series(dtype=str)
    df = df.loc[valid].copy()

    df["source_row_index"] = df["source_row_index"].astype(int)
    df["offer_id"] = df["city"] + "_" + df["day_type"] + "_" + df["source_row_index"].astype(str).str.zfill(5)
    df["real_sum"] = df["realSum"]
    df["two_night_total_eur"] = df["realSum"]                     # realSum = 2 guests x 2 nights, EUR (source docs)
    df["nightly_equivalent_eur"] = df["realSum"] / 2.0            # derived, NOT an observed nightly rate
    df["multi_listing_host"] = df["multi"].astype(bool)
    df["business_host"] = df["biz"].astype(bool)
    df["person_capacity"] = df["person_capacity"].astype(int)
    df["bedrooms"] = df["bedrooms"].astype(int)
    df = df.rename(columns={"dist": "dist_city_center_km", "metro_dist": "dist_metro_km"})
    df["is_studio"] = df["bedrooms"].eq(0)
    grp = df.groupby(["city", "day_type"])["two_night_total_eur"]
    q1, q3 = grp.transform(lambda s: s.quantile(0.25)), grp.transform(lambda s: s.quantile(0.75))
    df["price_outlier_iqr"] = df["two_night_total_eur"] > (q3 + 1.5 * (q3 - q1))   # upper Tukey fence per city/day type
    df["city"] = df["city"].str.title()   # display name; lower-case file key survives in offer_id / source_file
    df = df[SILVER_COLUMNS].sort_values("offer_id").reset_index(drop=True)
    report.update(rows_out=int(len(df)), rows_quarantined=int(len(quarantine)),
                  duplicate_offer_ids=int(df["offer_id"].duplicated().sum()),
                  exact_duplicate_content_rows=int(df.drop(columns=["offer_id", "source_row_index"]).duplicated().sum()),
                  price_outliers_flagged=int(df["price_outlier_iqr"].sum()),
                  studios=int(df["is_studio"].sum()), imputed_values=0)
    return df, quarantine, report


def build(raw_dir: Path | None = None, out_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    out_dir = out_dir or config.SILVER_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = read_raw(raw_dir)
    df, quarantine, report = clean(raw)
    df.to_parquet(out_dir / "airbnb_europe_master.parquet", index=False)
    df.to_csv(out_dir / "airbnb_europe_master.csv", index=False)
    quarantine.to_csv(out_dir / "quarantine_rejected_rows.csv", index=False)
    (out_dir / "silver_report.json").write_text(json.dumps(report, indent=2))
    return df, report


def load_to_postgres(conn, df: pd.DataFrame) -> int:
    """Replace silver.airbnb_europe_master with the dataframe (full refresh => idempotent)."""
    cols = ", ".join(SILVER_COLUMNS)
    conn.execute("TRUNCATE silver.airbnb_europe_master")
    out = df.copy()
    for c in out.select_dtypes("bool").columns:
        out[c] = out[c].map({True: "t", False: "f"})
    with conn.cursor().copy(f"COPY silver.airbnb_europe_master({cols}) FROM STDIN WITH (FORMAT csv)") as cp:
        cp.write(out.to_csv(index=False, header=False))
    conn.commit()
    return conn.execute("SELECT count(*) FROM silver.airbnb_europe_master").fetchone()[0]
