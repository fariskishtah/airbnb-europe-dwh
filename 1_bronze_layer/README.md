# Bronze layer
`validation/validate_sources.py` (20 files, identical header, MD5 vs Zenodo, no duplicates) · `ingestion/run_bronze.py` (manifest + idempotent raw-text load) · `validation/profile_data.py` (→ `docs/DATA_PROFILING.md`).
Outputs: `data/manifests/bronze_manifest.{csv,json}` (filename, city, day type, rows, columns, size, SHA-256, MD5, Zenodo MD5, timestamp, source), `bronze.raw_offers` (51,707 rows, all TEXT), `bronze.ingestion_log`.
Raw CSVs are never modified.
