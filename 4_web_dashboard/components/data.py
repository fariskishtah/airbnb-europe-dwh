"""Database access for the dashboard: read-only, parameterised, cached. No credentials in code."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from airbnb_dwh import config  # noqa: E402

VIEW = "gold.vw_offers_enriched"


@st.cache_resource(show_spinner=False)
def get_engine():
    # Read-only session: even a bug could not modify the warehouse from the dashboard.
    return create_engine(config.sqlalchemy_url(), pool_pre_ping=True,
                         connect_args={"options": "-c default_transaction_read_only=on -c statement_timeout=30000"})


@st.cache_data(ttl=600, show_spinner=False)
def _cached(sql: str, params_json: str) -> pd.DataFrame:
    with get_engine().connect() as c:
        return pd.read_sql(text(sql), c, params=json.loads(params_json))


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a parameterised SELECT. Values are always bound parameters, never string-formatted."""
    return _cached(sql, json.dumps(params or {}, sort_keys=True, default=str))


@dataclass
class Filters:
    cities: list[str] = field(default_factory=list)
    day_types: list[str] = field(default_factory=list)
    room_types: list[str] = field(default_factory=list)
    superhost: list[bool] = field(default_factory=list)
    price_min: float = 0.0
    price_max: float = 1e9
    cap_min: int = 1
    cap_max: int = 99

    def is_empty_selection(self) -> bool:
        return not (self.cities and self.day_types and self.room_types and self.superhost)

    def where(self) -> tuple[str, dict]:
        """WHERE clause against gold.vw_offers_enriched with bound parameters only."""
        sql = ("city = ANY(:cities) AND day_type = ANY(:days) AND room_type = ANY(:rooms) AND is_superhost = ANY(:sh) "
               "AND two_night_total_eur BETWEEN :pmin AND :pmax AND person_capacity BETWEEN :cmin AND :cmax")
        return sql, {"cities": list(self.cities), "days": list(self.day_types), "rooms": list(self.room_types),
                     "sh": list(self.superhost), "pmin": float(self.price_min), "pmax": float(self.price_max),
                     "cmin": int(self.cap_min), "cmax": int(self.cap_max)}


@st.cache_data(ttl=3600, show_spinner=False)
def dimension_options() -> dict:
    cities = query("SELECT city_name FROM gold.dim_city ORDER BY 1")["city_name"].tolist()
    days = query("SELECT day_type FROM gold.dim_day_type ORDER BY 1")["day_type"].tolist()
    rooms = query("SELECT room_type FROM gold.dim_room_type ORDER BY 1")["room_type"].tolist()
    r = query("SELECT floor(min(two_night_total_eur)) lo, ceil(max(two_night_total_eur)) hi, min(person_capacity) cmin, "
              "max(person_capacity) cmax FROM gold.fact_offer_observation").iloc[0]
    return {"cities": cities, "days": days, "rooms": rooms, "price": (float(r.lo), float(r.hi)),
            "cap": (int(r.cmin), int(r.cmax))}


def run(sql_body: str, f: Filters, extra: dict | None = None) -> pd.DataFrame:
    """Run `sql_body` where it contains the token {WHERE}, replaced with the bound-parameter filter clause."""
    where, params = f.where()
    params.update(extra or {})
    return query(sql_body.replace("{WHERE}", where), params)
