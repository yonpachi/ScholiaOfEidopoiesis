#!/usr/bin/env python3
"""SQL / CSV から data/game.db を再生成する。

正（Source of Truth）:
  - data/schema/*.sql  … テーブル定義（番号順に適用）
  - data/seeds/*.sql   … シード SQL（番号順に適用）
  - data/seeds/*.csv   … 未対応（テーブル定義後に拡張）

生成物:
  - data/game.db（.gitignore 対象）
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_DIR = DATA_DIR / "schema"
SEEDS_DIR = DATA_DIR / "seeds"
DB_PATH = DATA_DIR / "game.db"


def applySqlFiles(conn: sqlite3.Connection, directory: Path) -> None:
    if not directory.is_dir():
        return

    for path in sorted(directory.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        print(f"  applied: {path.relative_to(PROJECT_ROOT)}")


def buildDb() -> Path:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")

        print("Applying schema...")
        applySqlFiles(conn, SCHEMA_DIR)

        print("Applying seeds...")
        applySqlFiles(conn, SEEDS_DIR)

        conn.commit()
    finally:
        conn.close()

    return DB_PATH


def main() -> int:
    dbPath = buildDb()
    print(f"Created: {dbPath.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
