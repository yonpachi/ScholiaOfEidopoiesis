#!/usr/bin/env python3
"""Initialize or rebuild catalog/game.sqlite from schema.sql and views.sql."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "catalog"
DB_PATH = CATALOG_DIR / "game.sqlite"


def apply_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text(encoding="utf-8"))


def main() -> int:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        apply_sql_file(conn, CATALOG_DIR / "schema.sql")
        apply_sql_file(conn, CATALOG_DIR / "views.sql")
        conn.commit()
    finally:
        conn.close()
    print(f"initialized {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
