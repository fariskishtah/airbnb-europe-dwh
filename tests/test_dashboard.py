from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from components import data
from queries import catalog

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["1_Executive_Overview", "2_City_Intelligence", "3_Pricing_Analytics", "4_Property_Room_Insights",
         "5_Ratings_Location", "6_Geospatial_View", "7_Data_Quality_Pipeline", "8_SQL_Explorer"]


def full_filters(wh, **kw):
    f = data.Filters(cities=[r[0] for r in wh.execute("SELECT city_name FROM gold.dim_city").fetchall()],
                     day_types=["weekday", "weekend"], room_types=["Entire home/apt", "Private room", "Shared room"],
                     superhost=[True, False], price_min=0, price_max=1e9, cap_min=1, cap_max=99)
    for k, v in kw.items():
        setattr(f, k, v)
    return f


def test_kpis_match_silver(warehouse, silver_df):
    f = full_filters(warehouse)
    k = data.run("SELECT count(*) n, avg(two_night_total_eur) a, percentile_cont(0.5) WITHIN GROUP (ORDER BY two_night_total_eur) m, "
                 "avg(guest_satisfaction_overall) s, avg(cleanliness_rating) c FROM gold.vw_offers_enriched WHERE {WHERE}", f).iloc[0]
    assert k.n == len(silver_df)
    assert k.a == pytest.approx(silver_df.two_night_total_eur.mean()) and k.m == pytest.approx(silver_df.two_night_total_eur.median())
    assert k.s == pytest.approx(silver_df.guest_satisfaction_overall.mean()) and k.c == pytest.approx(silver_df.cleanliness_rating.mean())


def test_filters_change_results(warehouse, silver_df):
    f = full_filters(warehouse, cities=["Paris"], day_types=["weekend"], room_types=["Private room"], superhost=[True], price_min=100, price_max=300, cap_min=2, cap_max=4)
    n = data.run("SELECT count(*) n FROM gold.vw_offers_enriched WHERE {WHERE}", f)["n"][0]
    s = silver_df
    exp = s[(s.city == "Paris") & (s.day_type == "weekend") & (s.room_type == "Private room") & s.host_is_superhost
            & s.two_night_total_eur.between(100, 300) & s.person_capacity.between(2, 4)]
    assert 0 < n == len(exp)


def test_empty_results_handled(warehouse):
    f = full_filters(warehouse, price_min=1e8, price_max=1e9)
    assert data.run("SELECT count(*) n FROM gold.vw_offers_enriched WHERE {WHERE}", f)["n"][0] == 0
    assert full_filters(warehouse, cities=[]).is_empty_selection()
    assert data.run("SELECT city FROM gold.vw_offers_enriched WHERE {WHERE}", full_filters(warehouse, cities=[])).empty


def test_explorer_all_metric_group_combinations_execute(warehouse):
    f = full_filters(warehouse)
    for m in catalog.METRICS:
        for g in catalog.GROUPINGS:
            df = data.run(catalog.build_explorer_sql(m, g, None), f)
            assert len(df) >= 1 and "metric_value" in df.columns
    two = data.run(catalog.build_explorer_sql("Median two-night total (EUR)", "City", "Day type"), f)
    assert len(two) == 20


def test_explorer_rejects_invalid_inputs():
    for bad in [("Average two-night total (EUR)", "City; DROP TABLE gold.dim_city", None), ("1); DELETE FROM x;--", "City", None)]:
        with pytest.raises(KeyError):
            catalog.build_explorer_sql(*bad)


def test_dashboard_numbers_equal_sql_and_silver(warehouse, silver_df):
    f = full_filters(warehouse)
    dash = data.run("SELECT city, avg(two_night_total_eur) avg_eur FROM gold.vw_offers_enriched WHERE {WHERE} GROUP BY 1 ORDER BY 2 DESC", f)
    exp = silver_df.groupby("city").two_night_total_eur.mean().sort_values(ascending=False)
    assert dash.city.tolist() == exp.index.tolist()          # ranking identical
    assert dash.avg_eur.tolist() == pytest.approx(exp.tolist())


@pytest.mark.parametrize("page", PAGES)
def test_page_runs_without_exception(warehouse, page):
    at = AppTest.from_file(str(ROOT / "4_web_dashboard" / "pages" / f"{page}.py"), default_timeout=90)
    at.session_state["filters"] = full_filters(warehouse)
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_page_with_empty_filter_shows_warning_not_crash(warehouse):
    at = AppTest.from_file(str(ROOT / "4_web_dashboard" / "pages" / "1_Executive_Overview.py"), default_timeout=60)
    at.session_state["filters"] = full_filters(warehouse, cities=[])
    at.run()
    assert not at.exception and len(at.warning) == 1


def test_app_startup(warehouse):
    at = AppTest.from_file(str(ROOT / "4_web_dashboard" / "app.py"), default_timeout=120)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.sidebar.multiselect) >= 4
