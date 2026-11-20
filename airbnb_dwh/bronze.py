"""Bronze layer: source validation, manifest and idempotent raw loading (all values kept as text)."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import config, db


@dataclass
class SourceFile:
    source_file: str
    city: str
    day_type: str
    size_bytes: int
    row_count: int
    column_count: int
    sha256: str
    md5: str
    zenodo_md5: str | None
    md5_verified: bool | None
    header_ok: bool
    dataset_source: str = f"Zenodo DOI {config.SOURCE_DOI} (v2, {config.SOURCE_LICENSE})"


def safe_raw_path(name: str, raw_dir: Path | None = None) -> Path:
    """Resolve a raw file name and refuse anything outside the raw directory (path traversal guard)."""
    raw_dir = (raw_dir or config.RAW_DIR).resolve()
    p = (raw_dir / name).resolve()
    if p.parent != raw_dir or not config.FILENAME_RE.match(p.name):
        raise ValueError(f"unsafe or unexpected raw file path: {name!r}")
    return p


def discover(raw_dir: Path | None = None) -> list[Path]:
    raw_dir = raw_dir or config.RAW_DIR
    return sorted(p for p in raw_dir.glob("*.csv") if config.FILENAME_RE.match(p.name))


def file_hashes(path: Path) -> tuple[str, str]:
    s, m = hashlib.sha256(), hashlib.md5()  # noqa: S324 - md5 only to compare with Zenodo's published checksums
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            s.update(chunk)
            m.update(chunk)
    return s.hexdigest(), m.hexdigest()


def inspect_file(path: Path, zenodo: dict[str, str] | None = None) -> SourceFile:
    zenodo = config.zenodo_md5() if zenodo is None else zenodo
    match = config.FILENAME_RE.match(path.name)
    if not match:
        raise ValueError(f"unexpected file name {path.name}")
    sha, md5 = file_hashes(path)
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = sum(1 for _ in reader)
    z = zenodo.get(path.name)
    return SourceFile(
        source_file=path.name, city=match["city"], day_type=match["day"],
        size_bytes=path.stat().st_size, row_count=rows, column_count=len(header),
        sha256=sha, md5=md5, zenodo_md5=z, md5_verified=(md5 == z) if z else None,
        header_ok=header == config.EXPECTED_HEADER,
    )


def build_manifest(raw_dir: Path | None = None) -> list[SourceFile]:
    files = discover(raw_dir)
    zen = config.zenodo_md5()
    return [inspect_file(p, zen) for p in files]


def validate_sources(raw_dir: Path | None = None, expected_files: int = 20) -> list[str]:
    """Return a list of problems (empty list = all source checks pass)."""
    problems: list[str] = []
    manifest = build_manifest(raw_dir)
    if len(manifest) != expected_files:
        problems.append(f"expected {expected_files} CSV files, found {len(manifest)}")
    seen: dict[str, str] = {}
    for m in manifest:
        if m.row_count == 0:
            problems.append(f"{m.source_file}: empty")
        if not m.header_ok:
            problems.append(f"{m.source_file}: header differs from the common schema")
        if m.md5_verified is False:
            problems.append(f"{m.source_file}: MD5 does not match Zenodo record")
        if m.md5_verified is None:
            problems.append(f"{m.source_file}: no Zenodo MD5 available to verify")
        if m.sha256 in seen:
            problems.append(f"{m.source_file}: duplicate content of {seen[m.sha256]}")
        seen[m.sha256] = m.source_file
    return problems


def write_manifest(manifest: list[SourceFile], run_id: str) -> None:
    config.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = [{**asdict(m), "ingestion_timestamp_utc": ts, "run_id": run_id} for m in manifest]
    with open(config.MANIFEST_DIR / "bronze_manifest.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summary = {
        "run_id": run_id, "generated_utc": ts, "dataset": config.SOURCE_URL, "license": config.SOURCE_LICENSE,
        "files": len(rows), "total_rows": sum(r["row_count"] for r in rows),
        "all_md5_verified": all(r["md5_verified"] for r in rows),
        "common_schema_in_all_files": all(r["header_ok"] for r in rows),
        "common_header": config.EXPECTED_HEADER,
        "manifest": rows,
    }
    (config.MANIFEST_DIR / "bronze_manifest.json").write_text(json.dumps(summary, indent=2))


def load_bronze(conn, manifest: list[SourceFile], run_id: str, force: bool = False,
                raw_dir: Path | None = None) -> dict:
    """Idempotently load raw CSV text into bronze.raw_offers.

    - same file + same hash already loaded -> skipped (no duplicates on re-run)
    - same file name but changed hash      -> replaced
    - same hash under a different name     -> rejected (duplicate file ingestion)
    """
    raw_dir = raw_dir or config.RAW_DIR
    db.run_sql_file(conn, config.DDL_DIR / "01_bronze_silver_tables.sql")
    conn.commit()
    stats = {"loaded": [], "skipped": [], "replaced": []}
    cols = ", ".join(config.BRONZE_COLUMNS)
    for m in manifest:
        existing = conn.execute("SELECT sha256 FROM bronze.ingestion_log WHERE source_file=%s", (m.source_file,)).fetchone()
        dup = conn.execute("SELECT source_file FROM bronze.ingestion_log WHERE sha256=%s AND source_file<>%s",
                           (m.sha256, m.source_file)).fetchone()
        if dup:
            raise ValueError(f"{m.source_file} has identical content to already-ingested {dup[0]}")
        if existing and existing[0] == m.sha256 and not force:
            stats["skipped"].append(m.source_file)
            continue
        if existing:
            conn.execute("DELETE FROM bronze.ingestion_log WHERE source_file=%s", (m.source_file,))  # cascades rows
            stats["replaced"].append(m.source_file)
        conn.execute(
            """INSERT INTO bronze.ingestion_log(source_file,city,day_type,sha256,md5,zenodo_md5,md5_verified,
                   size_bytes,row_count,column_count,run_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (m.source_file, m.city, m.day_type, m.sha256, m.md5, m.zenodo_md5, m.md5_verified,
             m.size_bytes, m.row_count, m.column_count, run_id),
        )
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS _stage (ord serial, " +
                     ", ".join(f"{c} text" for c in config.BRONZE_COLUMNS) + ") ON COMMIT DROP")
        conn.execute("TRUNCATE _stage RESTART IDENTITY")
        path = safe_raw_path(m.source_file, raw_dir)
        with open(path, "r", encoding="utf-8", newline="") as fh, \
                conn.cursor().copy(f"COPY _stage({cols}) FROM STDIN WITH (FORMAT csv, HEADER true, NULL '\u0001')") as cp:
            while chunk := fh.read(1 << 20):
                cp.write(chunk)
        conn.execute(f"INSERT INTO bronze.raw_offers(source_file, source_row_number, {cols}) "
                     f"SELECT %s, ord, {cols} FROM _stage ORDER BY ord", (m.source_file,))
        conn.commit()
        stats["loaded"].append(m.source_file)
    return stats


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
