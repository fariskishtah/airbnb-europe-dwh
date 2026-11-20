from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import psycopg
from sqlalchemy import create_engine

from . import config


def connect(url: str | None = None, autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(config.database_url(url), autocommit=autocommit)


def engine(url: str | None = None):
    return create_engine(config.sqlalchemy_url(url), pool_pre_ping=True)


def run_sql_file(conn: psycopg.Connection, path: Path) -> None:
    """Execute a .sql file (multiple statements) inside the current transaction."""
    conn.execute(Path(path).read_text())


@contextmanager
def pipeline_step(conn: psycopg.Connection, run_id: str, layer: str, step: str):
    """Record a pipeline step in meta.pipeline_run (survives warehouse rebuilds)."""
    conn.execute("CREATE SCHEMA IF NOT EXISTS meta")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS meta.pipeline_run(
            id bigserial PRIMARY KEY, run_id text NOT NULL, layer text NOT NULL, step text NOT NULL,
            status text NOT NULL, rows_affected bigint, started_at timestamptz NOT NULL,
            finished_at timestamptz, detail text)"""
    )
    conn.commit()
    holder = {"rows": None, "detail": None}
    cur = conn.execute(
        "INSERT INTO meta.pipeline_run(run_id,layer,step,status,started_at) VALUES(%s,%s,%s,'RUNNING',now()) RETURNING id",
        (run_id, layer, step),
    )
    rid = cur.fetchone()[0]
    conn.commit()
    try:
        yield holder
        conn.commit()
        conn.execute(
            "UPDATE meta.pipeline_run SET status='SUCCESS', finished_at=now(), rows_affected=%s, detail=%s WHERE id=%s",
            (holder["rows"], holder["detail"], rid),
        )
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        conn.execute(
            "UPDATE meta.pipeline_run SET status='FAILED', finished_at=now(), detail=%s WHERE id=%s",
            (str(exc)[:500], rid),
        )
        conn.commit()
        raise
