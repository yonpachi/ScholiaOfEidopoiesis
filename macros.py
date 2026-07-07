"""MkDocs ビルド時に constants/*.json を Jinja 変数として登録する。"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONSTANTS_DIR = PROJECT_ROOT / "constants"


def define_env(env):
    """mkdocs-macros-plugin のエントリポイント。"""
    if not CONSTANTS_DIR.is_dir():
        return

    for path in sorted(CONSTANTS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as file:
            env.variables[path.stem] = json.load(file)
