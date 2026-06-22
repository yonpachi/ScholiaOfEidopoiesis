#!/usr/bin/env python3
"""One-shot migration from Notion HTML export CSVs into catalog/game.sqlite."""

from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_ROOT = REPO_ROOT / "html" / "錬金TRPG「想成のスコーリア」"
CATALOG_DIR = REPO_ROOT / "catalog"
DB_PATH = CATALOG_DIR / "game.sqlite"


def make_id(prefix: str, name: str) -> str:
    return f"{prefix}_{name}"


def find_csv(fragment: str) -> Path:
    matches = sorted(HTML_ROOT.rglob(f"*{fragment}*.csv"))
    if not matches:
        raise FileNotFoundError(f"CSV not found for fragment: {fragment}")
    return matches[0]


def parse_relation(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    match = re.match(r"^(.+?)\s*\(", value)
    if match:
        return match.group(1).strip()
    return value


def flag_int(value: str) -> int:
    return 1 if (value or "").strip() == "1" else 0


def optional_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def apply_sql_file(conn: sqlite3.Connection, path: Path) -> None:
    conn.executescript(path.read_text(encoding="utf-8"))


def init_db(conn: sqlite3.Connection) -> None:
    apply_sql_file(conn, CATALOG_DIR / "schema.sql")
    apply_sql_file(conn, CATALOG_DIR / "views.sql")


def clear_data(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DELETE FROM item_tags;
        DELETE FROM items;
        DELETE FROM tags;
        DELETE FROM tag_kinds;
        DELETE FROM marks;
        DELETE FROM weapons;
        DELETE FROM armor;
        DELETE FROM terms;
        DELETE FROM scorions;
        """
    )


def migrate_tag_kinds(conn: sqlite3.Connection) -> dict[str, str]:
    path = find_csv("タグ種別DB")
    name_to_id: dict[str, str] = {}
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name:
            continue
        kind_id = make_id("kind", name)
        conn.execute(
            "INSERT INTO tag_kinds (id, name) VALUES (?, ?)",
            (kind_id, name),
        )
        name_to_id[name] = kind_id
    return name_to_id


def migrate_marks(conn: sqlite3.Connection) -> None:
    path = find_csv("印記一覧DB")
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO marks (id, name, effect, decay)
            VALUES (?, ?, ?, ?)
            """,
            (
                make_id("mark", name),
                name,
                (row.get("効果") or "").strip(),
                (row.get("減衰") or "").strip(),
            ),
        )


def migrate_tags(conn: sqlite3.Connection, kind_name_to_id: dict[str, str]) -> dict[str, str]:
    path = find_csv("タグ一覧DB")
    name_to_id: dict[str, str] = {}
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name:
            continue
        kind_name = parse_relation(row.get("種別") or "")
        kind_id = kind_name_to_id.get(kind_name) if kind_name else None
        tag_id = make_id("tag", name)
        conn.execute(
            """
            INSERT INTO tags (
                id, name, mana, kind_id, note, effect, restriction,
                flag_fire, flag_earth, flag_water, flag_wind, flag_dark, flag_light
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tag_id,
                name,
                (row.get("マナ") or "").strip(),
                kind_id,
                (row.get("備考") or "").strip(),
                (row.get("効果") or "").strip(),
                (row.get("制限") or "").strip(),
                flag_int(row.get("火") or ""),
                flag_int(row.get("土") or ""),
                flag_int(row.get("水") or ""),
                flag_int(row.get("風") or ""),
                flag_int(row.get("闇") or ""),
                flag_int(row.get("光") or ""),
            ),
        )
        name_to_id[name] = tag_id
    return name_to_id


def migrate_items(conn: sqlite3.Connection, tag_name_to_id: dict[str, str]) -> None:
    path = find_csv("アイテム一覧DB")
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name or name == "アイテム名":
            continue
        item_id = make_id("item", name)
        conn.execute(
            """
            INSERT INTO items (
                id, name, timing, kind, difficulty, effect, note,
                creation_mana, entity_strength, strength, formula_strength
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                name,
                (row.get("タイミング") or "").strip(),
                (row.get("種別") or "").strip(),
                optional_int(row.get("難易度") or ""),
                (row.get("効果") or "").strip(),
                (row.get("備考") or "").strip(),
                (row.get("作成マナ") or "").strip(),
                (row.get("実体強度") or "").strip(),
                (row.get("強度") or "").strip(),
                (row.get("術式強度") or "").strip(),
            ),
        )
        tags_cell = row.get("タグ") or ""
        for part in tags_cell.split(","):
            tag_name = parse_relation(part)
            if not tag_name:
                continue
            tag_id = tag_name_to_id.get(tag_name)
            if tag_id is None:
                print(f"warning: unknown tag {tag_name!r} for item {name!r}", file=sys.stderr)
                continue
            conn.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES (?, ?)",
                (item_id, tag_id),
            )


def migrate_weapons(conn: sqlite3.Connection) -> None:
    path = find_csv("武器一覧DB")
    for row in read_csv(path):
        name = (row.get("レシピ") or "").strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO weapons (
                id, name, recipe, cost, flavor, effect, attribute, grade, weight,
                flag_fire, flag_earth, flag_water, flag_wind, flag_dark, flag_light
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                make_id("weapon", name),
                name,
                name,
                (row.get("コスト") or "").strip(),
                (row.get("フレーバー") or "").strip(),
                (row.get("効果") or "").strip(),
                (row.get("属性") or "").strip(),
                optional_int(row.get("等級") or ""),
                (row.get("重量") or "").strip(),
                flag_int(row.get("火") or ""),
                flag_int(row.get("土") or ""),
                flag_int(row.get("水") or ""),
                flag_int(row.get("風") or ""),
                flag_int(row.get("闇") or ""),
                flag_int(row.get("光") or ""),
            ),
        )


def migrate_armor(conn: sqlite3.Connection) -> None:
    path = find_csv("防具一覧DB")
    for row in read_csv(path):
        name = (row.get("レシピ") or "").strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO armor (
                id, name, recipe, cost, effect, grade, weight,
                flag_fire, flag_earth, flag_water, flag_wind, flag_dark, flag_light
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                make_id("armor", name),
                name,
                name,
                (row.get("コスト") or "").strip(),
                (row.get("効果") or "").strip(),
                optional_int(row.get("等級") or ""),
                (row.get("重量") or "").strip(),
                flag_int(row.get("火") or ""),
                flag_int(row.get("土") or ""),
                flag_int(row.get("水") or ""),
                flag_int(row.get("風") or ""),
                flag_int(row.get("闇") or ""),
                flag_int(row.get("光") or ""),
            ),
        )


def migrate_terms(conn: sqlite3.Connection) -> None:
    path = find_csv("用語一覧DB")
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO terms (id, name, body, categories)
            VALUES (?, ?, ?, ?)
            """,
            (
                make_id("term", name),
                name,
                (row.get("テキスト") or "").strip(),
                (row.get("マルチセレクト") or "").strip(),
            ),
        )


def migrate_scorions(conn: sqlite3.Connection) -> None:
    path = find_csv("スコーリオンDB")
    for row in read_csv(path):
        name = (row.get("名前") or "").strip()
        if not name:
            continue
        conn.execute(
            """
            INSERT INTO scorions (
                id, name, mana_bias, recommended_difficulty,
                enemy_tendency, material_tendency, adjacency_effect
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                make_id("scorion", name),
                name,
                (row.get("マナ傾向") or "").strip(),
                (row.get("推奨難易度") or "").strip(),
                (row.get("敵傾向") or "").strip(),
                (row.get("素材傾向") or "").strip(),
                (row.get("隣接影響") or "").strip(),
            ),
        )


def main() -> int:
    if not HTML_ROOT.is_dir():
        print(f"error: html export not found at {HTML_ROOT}", file=sys.stderr)
        return 1

    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        init_db(conn)
        clear_data(conn)
        kind_ids = migrate_tag_kinds(conn)
        migrate_marks(conn)
        tag_ids = migrate_tags(conn, kind_ids)
        migrate_items(conn, tag_ids)
        migrate_weapons(conn)
        migrate_armor(conn)
        migrate_terms(conn)
        migrate_scorions(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"migrated catalog -> {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
