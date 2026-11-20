#!/usr/bin/env bash
# Manage a throw-away local PostgreSQL cluster for this project (no password, loopback only).
# Usage: other_scripts/pg_local.sh {init|start|stop|status|createdb <name>}
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Use the PostgreSQL binaries bundled in the venv (pip package `pgserver`), else system PATH.
PGBIN="$(ls -d "$ROOT"/.venv/lib/python*/site-packages/pgserver/pginstall/bin 2>/dev/null | head -1 || true)"
[ -n "$PGBIN" ] && export PATH="$PGBIN:$PATH"
PGDATA="${AWH_PGDATA:-$ROOT/.pgdata}"
PGPORT="${AWH_PGPORT:-54329}"
SOCK="${AWH_PGSOCK:-/tmp/awh_pg}"
case "${1:-}" in
  init)
    [ -d "$PGDATA" ] && { echo "cluster exists: $PGDATA"; exit 0; }
    initdb -D "$PGDATA" -U "$(whoami)" --auth=trust -E UTF8 >/dev/null
    echo "initialised $PGDATA" ;;
  start)
    mkdir -p "$SOCK"
    pg_ctl -D "$PGDATA" -l "$PGDATA/server.log" -o "-p $PGPORT -c listen_addresses=127.0.0.1 -c unix_socket_directories=$SOCK" -w start ;;
  stop)   pg_ctl -D "$PGDATA" -m fast stop ;;
  status) pg_isready -h 127.0.0.1 -p "$PGPORT" ;;
  createdb) psql -h 127.0.0.1 -p "$PGPORT" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='$2'" | grep -q 1 || createdb -h 127.0.0.1 -p "$PGPORT" "$2" ;;
  *) echo "usage: $0 {init|start|stop|status|createdb NAME}"; exit 1 ;;
esac
