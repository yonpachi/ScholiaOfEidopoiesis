"""sim/partN/run.py を番号順にすべて実行する。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import resolve_out_dir  # noqa: E402

SIM_DIR = Path(__file__).resolve().parent
ROOT_DIR = SIM_DIR.parent
PART_DIR_PATTERN = re.compile(r"^part(\d+)$")


def discover_part_runs() -> list[Path]:
    """sim/partN/run.py を番号順に列挙する。part4 追加時も自動で含まれる。"""
    found: list[tuple[int, Path]] = []
    for run_py in SIM_DIR.glob("part*/run.py"):
        match = PART_DIR_PATTERN.match(run_py.parent.name)
        if match is None:
            continue
        found.append((int(match.group(1)), run_py))
    found.sort(key=lambda item: item[0])
    return [run_py for _, run_py in found]


def main() -> None:
    p = argparse.ArgumentParser(
        description="sim/partN/run.py を番号順にすべて実行する（出力は1フォルダに集約）"
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="output dir (default: result/<timestamp> at project root)",
    )
    args = p.parse_args()

    runs = discover_part_runs()
    if not runs:
        print("sim/partN/run.py が見つかりません。")
        sys.exit(1)

    out_dir = resolve_out_dir(args.out_dir)
    print(f"出力: {out_dir}")
    print(f"実行対象: {len(runs)} Part")

    for index, run_py in enumerate(runs, start=1):
        part_name = run_py.parent.name
        print(f"\n=== [{index}/{len(runs)}] {part_name} ===")
        proc = subprocess.run(
            [sys.executable, str(run_py), "--out-dir", str(out_dir)],
            cwd=str(ROOT_DIR),
        )
        if proc.returncode != 0:
            print(
                f"エラー: {part_name} が終了コード {proc.returncode} で終了しました。"
            )
            sys.exit(proc.returncode)

    print(f"\n全 {len(runs)} Part 完了。出力: {out_dir}")


if __name__ == "__main__":
    main()
