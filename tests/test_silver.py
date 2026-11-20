import pandas as pd
import pytest

from airbnb_dwh import silver


def test_schema(silver_df):
    assert list(silver_df.columns) == silver.SILVER_COLUMNS
    assert str(silver_df["real_sum"].dtype) == "float64" and str(silver_df["person_capacity"].dtype).startswith("int")
    assert silver_df["host_is_superhost"].dtype == bool


def test_row_reconciliation_with_raw(silver_df):
    raw = silver.read_raw()
    assert len(raw) == len(silver_df) == 51707
    assert silver_df.groupby("source_file").size().to_dict() == raw.groupby("source_file").size().to_dict()


def test_lineage_and_uniqueness(silver_df):
    assert silver_df["offer_id"].is_unique
    assert not silver_df.duplicated(["source_file", "source_row_index"]).any()
    row = silver_df[silver_df.offer_id == "amsterdam_weekday_00000"].iloc[0]
    assert row.source_file == "amsterdam_weekdays.csv" and row.source_row_index == 0 and row.city == "Amsterdam"
    assert row.real_sum == pytest.approx(194.03369812293488)


def test_price_semantics(silver_df):
    assert (silver_df.two_night_total_eur == silver_df.real_sum).all()
    assert (silver_df.nightly_equivalent_eur * 2 - silver_df.two_night_total_eur).abs().max() < 1e-9


def test_category_standardisation(silver_df):
    assert set(silver_df.room_type) == {"Entire home/apt", "Private room", "Shared room"}
    assert set(silver_df.day_type) == {"weekday", "weekend"}
    assert silver_df.city.str.istitle().all()
    assert (silver_df.room_shared == (silver_df.room_type == "Shared room")).all()


def test_no_nulls_and_valid_ranges(silver_df):
    assert not silver_df.isna().any().any()
    assert (silver_df.real_sum > 0).all() and silver_df.guest_satisfaction_overall.between(0, 100).all()
    assert silver_df.cleanliness_rating.between(0, 10).all() and (silver_df.bedrooms >= 0).all()


def _raw_row(**over):
    base = {"source_row_index": "0", "realSum": "100.0", "room_type": "Private room", "room_shared": "False", "room_private": "True",
            "person_capacity": "2.0", "host_is_superhost": "False", "multi": "0", "biz": "0", "cleanliness_rating": "9.0",
            "guest_satisfaction_overall": "90.0", "bedrooms": "1", "dist": "1.0", "metro_dist": "0.5", "attr_index": "100",
            "attr_index_norm": "5", "rest_index": "100", "rest_index_norm": "5", "lng": "4.9", "lat": "52.37",
            "source_file": "amsterdam_weekdays.csv", "city": "amsterdam", "day_type": "weekday"}
    base.update(over)
    return base


def test_cleaning_quarantines_invalid_rows_instead_of_dropping_silently():
    raw = pd.DataFrame([_raw_row(), _raw_row(source_row_index="1", realSum="-5"), _raw_row(source_row_index="2", lat="10.0"),
                        _raw_row(source_row_index="3", guest_satisfaction_overall="140"), _raw_row(source_row_index="4", room_type="Castle", room_shared="False")])
    clean, quarantine, rep = silver.clean(raw)
    assert len(clean) == 1 and len(quarantine) == 4 and rep["rows_in"] == 5
    assert set(quarantine.source_row_index) == {"1", "2", "3", "4"}
    assert "price_positive" in quarantine.loc[quarantine.source_row_index == "1", "failed_rules"].iloc[0]


def test_strict_boolean_parsing_rejects_garbage():
    raw = pd.DataFrame([_raw_row(host_is_superhost="maybe")])
    with pytest.raises(ValueError):
        silver.clean(raw)


def test_duplicate_detection_reports_exact_duplicates():
    raw = pd.DataFrame([_raw_row(), _raw_row(source_row_index="1")])  # same content, different index
    _, _, rep = silver.clean(raw)
    assert rep["exact_duplicate_content_rows"] == 1 and rep["duplicate_offer_ids"] == 0


def test_build_is_deterministic(silver_df):
    raw = silver.read_raw()
    again, _, _ = silver.clean(raw)
    pd.testing.assert_frame_equal(silver_df.reset_index(drop=True), again.reset_index(drop=True))
