import csv
import shutil

import pytest

from airbnb_dwh import bronze, config


def test_file_discovery_finds_20_files():
    files = bronze.discover()
    assert len(files) == 20
    assert {p.name.split("_")[0] for p in files} == {"amsterdam", "athens", "barcelona", "berlin", "budapest", "lisbon", "london", "paris", "rome", "vienna"}


def test_manifest_validation_all_sources_pass():
    assert bronze.validate_sources() == []
    m = bronze.build_manifest()
    assert sum(x.row_count for x in m) == 51707
    assert all(x.md5_verified for x in m) and all(x.header_ok for x in m)
    assert all(x.column_count == 20 for x in m)


def test_manifest_flags_missing_files(tmp_path):
    shutil.copy(config.RAW_DIR / "rome_weekdays.csv", tmp_path / "rome_weekdays.csv")
    problems = bronze.validate_sources(tmp_path)
    assert any("expected 20" in p for p in problems)


def test_raw_files_unmodified_checksums_match_zenodo():
    z = config.zenodo_md5()
    for p in bronze.discover():
        assert bronze.file_hashes(p)[1] == z[p.name]


def test_bronze_preserves_raw_values_exactly(warehouse):
    # every raw value of every file equals the text stored in bronze.raw_offers
    for p in bronze.discover():
        with open(p, newline="") as fh:
            r = csv.reader(fh)
            next(r)
            rows = list(r)
        db_rows = warehouse.execute(
            "SELECT source_row_index, realsum, room_type, room_shared, host_is_superhost, lat, lng, guest_satisfaction_overall "
            "FROM bronze.raw_offers WHERE source_file=%s ORDER BY source_row_number", (p.name,)).fetchall()
        assert len(db_rows) == len(rows)
        for src, got in zip(rows, db_rows):
            assert [src[0], src[1], src[2], src[3], src[6], src[19], src[18], src[10]] == list(got)


def test_bronze_row_counts_match_manifest(warehouse):
    n = warehouse.execute("SELECT count(*) FROM bronze.raw_offers").fetchone()[0]
    assert n == 51707
    assert warehouse.execute("SELECT count(*) FROM bronze.ingestion_log").fetchone()[0] == 20


def test_rerun_does_not_duplicate(warehouse):
    stats = bronze.load_bronze(warehouse, bronze.build_manifest(), "rerun")
    assert stats["loaded"] == [] and len(stats["skipped"]) == 20
    assert warehouse.execute("SELECT count(*) FROM bronze.raw_offers").fetchone()[0] == 51707


def test_duplicate_file_content_is_rejected(warehouse, tmp_path):
    shutil.copy(config.RAW_DIR / "rome_weekdays.csv", tmp_path / "zzz_weekdays.csv")
    m = bronze.inspect_file(tmp_path / "zzz_weekdays.csv")
    with pytest.raises(ValueError, match="identical content"):
        bronze.load_bronze(warehouse, [m], "dup", raw_dir=tmp_path)
    warehouse.rollback()
