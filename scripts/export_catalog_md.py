#!/usr/bin/env python3
"""Export catalog/game.sqlite list views to Markdown for MkDocs."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = REPO_ROOT / "catalog"
DB_PATH = CATALOG_DIR / "game.sqlite"
OUTPUT_DIR = REPO_ROOT / "docs" / "catalog"

AUTO_GENERATED_NOTE = (
    "> **自動生成ファイル** — 直接編集しないこと。"
    " データの正本は `catalog/game.sqlite` です。"
    " 再生成: `python scripts/export_catalog_md.py`"
)

EXPORTS: list[tuple[str, str, str]] = [
    ("marks.md", "印記一覧", "v_marks_list"),
    ("tags.md", "タグ一覧", "v_tags_list"),
    ("items.md", "アイテム", "v_items_list"),
    ("weapons_armor.md", "武器・防具", "__weapons_armor__"),
    ("scorions.md", "スコーリオン", "v_scorions_list"),
    ("terms.md", "用語集", "v_terms_list"),
]

COLUMN_LABELS: dict[str, str] = {
    "id": "ID",
    "name": "名前",
    "effect": "効果",
    "decay": "減衰",
    "mana": "マナ",
    "kind_name": "種別",
    "note": "備考",
    "restriction": "制限",
    "flag_fire": "火",
    "flag_earth": "地",
    "flag_water": "水",
    "flag_wind": "風",
    "flag_dark": "闇",
    "flag_light": "光",
    "timing": "タイミング",
    "kind": "分類",
    "difficulty": "難易度",
    "creation_mana": "作成マナ",
    "entity_strength": "実体強度",
    "strength": "強度",
    "formula_strength": "式強度",
    "tag_names": "タグ",
    "recipe": "レシピ",
    "cost": "コスト",
    "flavor": "フレーバー",
    "attribute": "属性",
    "grade": "等級",
    "weight": "重量",
    "body": "本文",
    "categories": "カテゴリ",
    "mana_bias": "マナ偏り",
    "recommended_difficulty": "推奨難易度",
    "enemy_tendency": "敵傾向",
    "material_tendency": "素材傾向",
    "adjacency_effect": "隣接効果",
}


def escape_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("|", "\\|").replace("\n", "<br>")
    return text


def format_header(column: str) -> str:
    return COLUMN_LABELS.get(column, column)


def rows_to_markdown_table(columns: list[str], rows: list[tuple[object, ...]]) -> str:
    if not rows:
        return "_（データなし）_"

    headers = [format_header(col) for col in columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = [escape_cell(value) for value in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fetch_view(conn: sqlite3.Connection, view_name: str) -> tuple[list[str], list[tuple[object, ...]]]:
    cursor = conn.execute(f"SELECT * FROM {view_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


def fetch_weapons_armor(conn: sqlite3.Connection) -> str:
    sections: list[str] = []
    for title, view_name in [("武器", "v_weapons_list"), ("防具", "v_armor_list")]:
        columns, rows = fetch_view(conn, view_name)
        sections.append(f"## {title}\n\n{rows_to_markdown_table(columns, rows)}")
    return "\n\n".join(sections)


def write_page(path: Path, title: str, body: str) -> None:
    content = f"# {title}\n\n{AUTO_GENERATED_NOTE}\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def export_catalog(db_path: Path, output_dir: Path) -> int:
    if not db_path.is_file():
        print(f"skip: {db_path} not found", file=sys.stderr)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        for filename, title, source in EXPORTS:
            out_path = output_dir / filename
            if source == "__weapons_armor__":
                body = fetch_weapons_armor(conn)
            else:
                columns, rows = fetch_view(conn, source)
                body = rows_to_markdown_table(columns, rows)
            write_page(out_path, title, body)
            print(f"wrote {out_path.relative_to(REPO_ROOT)}")
    finally:
        conn.close()

    return 0


def main() -> int:
    try:
        return export_catalog(DB_PATH, OUTPUT_DIR)
    except sqlite3.Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
