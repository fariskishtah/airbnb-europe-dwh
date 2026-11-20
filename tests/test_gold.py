import pandas as pd
import pytest

TABLES = ["dim_city", "dim_day_type", "dim_room_type", "dim_host_status", "dim_source_file", "fact_offer_observation"]


def q(wh, sql, *a):
    return wh.execute(sql, a).fetchall()


def test_tables_and_row_counts(warehouse):
    names = {r[0] for r in q(warehouse, "SELECT table_name FROM information_schema.tables WHERE table_schema='gold' AND table_type='BASE TABLE'")}
    assert set(TABLES) <= names
    c = warehouse.run_stats["gold"]
    assert c == {"dim_city": 10, "dim_day_type": 2, "dim_room_type": 3, "dim_host_status": 6, "dim_source_file": 20, "fact_offer_observation": 51707}


def test_primary_keys_on_all_tables(warehouse):
    pks = {r[0] for r in q(warehouse, "SELECT cl.relname FROM pg_constraint c JOIN pg_class cl ON cl.oid=c.conrelid JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='gold' AND c.contype='p'")}
    assert pks == set(TABLES)


def test_foreign_keys_form_star(warehouse):
    fks = q(warehouse, """SELECT cl.relname, ref.relname FROM pg_constraint c JOIN pg_class cl ON cl.oid=c.conrelid
        JOIN pg_class ref ON ref.oid=c.confrelid JOIN pg_namespace n ON n.oid=cl.relnamespace WHERE n.nspname='gold' AND c.contype='f'""")
    fact = {r[1] for r in fks if r[0] == "fact_offer_observation"}
    assert fact == {"dim_city", "dim_day_type", "dim_room_type", "dim_host_status", "dim_source_file"}


def test_unique_constraint_blocks_duplicate_grain(warehouse):
    import psycopg
    with pytest.raises(psycopg.errors.UniqueViolation):
        warehouse.execute("INSERT INTO gold.fact_offer_observation SELECT * FROM gold.fact_offer_observation LIMIT 1")
    warehouse.rollback()


def test_foreign_key_blocks_orphans(warehouse):
    import psycopg
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        warehouse.execute("""INSERT INTO gold.fact_offer_observation SELECT 99999999, 'x', 999, day_type_key, room_type_key, host_status_key,
            source_file_key, 99999999, two_night_total_eur, nightly_equivalent_eur, person_capacity, bedrooms, cleanliness_rating,
            guest_satisfaction_overall, dist_city_center_km, dist_metro_km, attr_index, attr_index_norm, rest_index, rest_index_norm, lat, lng,
            is_studio, price_outlier_iqr FROM gold.fact_offer_observation LIMIT 1""")
    warehouse.rollback()


def test_no_unsupported_dimensions(warehouse):
    names = {r[0] for r in q(warehouse, "SELECT table_name FROM information_schema.tables WHERE table_schema='gold'")}
    assert not any(n in names for n in ["dim_date", "dim_host", "dim_property_type"])


def test_fact_grain_one_row_per_source_row(warehouse):
    assert q(warehouse, "SELECT count(*) - count(DISTINCT (source_file_key, source_row_index)) FROM gold.fact_offer_observation")[0][0] == 0


def test_layer_reconciliation(warehouse):
    rows = dict(q(warehouse, "SELECT object, row_count FROM gold.vw_layer_reconciliation"))
    assert set(rows.values()) == {51707}


def test_all_dq_checks_pass(warehouse):
    failed = [c for c in warehouse.run_stats["checks"] if c.status != "PASS"]
    assert not failed, failed
    assert len(warehouse.run_stats["checks"]) >= 25


def test_city_aggregates_match_pandas(warehouse, silver_df):
    sql = pd.DataFrame(q(warehouse, "SELECT city, observations, avg_two_night_total_eur, median_two_night_total_eur, avg_guest_satisfaction, avg_cleanliness FROM gold.vw_city_kpis"),
                       columns=["city", "n", "avg", "med", "sat", "clean"]).set_index("city").sort_index()
    g = silver_df.groupby("city")
    exp = pd.DataFrame({"n": g.size(), "avg": g.two_night_total_eur.mean(), "med": g.two_night_total_eur.median(),
                        "sat": g.guest_satisfaction_overall.mean(), "clean": g.cleanliness_rating.mean()}).sort_index()
    pd.testing.assert_frame_equal(sql.astype(float), exp.astype(float), rtol=1e-9, atol=1e-9, check_names=False)


def test_weekend_premium_matches_pandas(warehouse, silver_df):
    sql = {r[0]: r[1] for r in q(warehouse, "SELECT city, avg_weekend_diff_pct FROM gold.vw_weekend_premium")}
    m = silver_df.groupby(["city", "day_type"]).two_night_total_eur.mean().unstack()
    exp = (100 * (m.weekend / m.weekday - 1)).to_dict()
    for c, v in exp.items():
        assert sql[c] == pytest.approx(v, rel=1e-9)


def test_room_type_stats_match_pandas(warehouse, silver_df):
    sql = {r[0]: (r[1], r[2], r[3]) for r in q(warehouse, "SELECT room_type, observations, avg_two_night_total_eur, median_two_night_total_eur FROM gold.vw_room_type_stats")}
    g = silver_df.groupby("room_type").two_night_total_eur
    for rt in sql:
        assert sql[rt][0] == g.size()[rt]
        assert sql[rt][1] == pytest.approx(g.mean()[rt]) and sql[rt][2] == pytest.approx(g.median()[rt])


def test_surrogate_keys_stable_across_rebuild(warehouse):
    from airbnb_dwh import gold
    before = q(warehouse, "SELECT city_key, city_name FROM gold.dim_city ORDER BY 1")
    sample = q(warehouse, "SELECT offer_key, offer_id FROM gold.fact_offer_observation WHERE offer_key IN (1, 25000, 51707) ORDER BY 1")
    gold.build_gold(warehouse)
    assert before == q(warehouse, "SELECT city_key, city_name FROM gold.dim_city ORDER BY 1")
    assert sample == q(warehouse, "SELECT offer_key, offer_id FROM gold.fact_offer_observation WHERE offer_key IN (1, 25000, 51707) ORDER BY 1")
    assert q(warehouse, "SELECT count(*) FROM gold.fact_offer_observation")[0][0] == 51707
