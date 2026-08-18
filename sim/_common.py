"""Shared helpers for sim/partN run.py scripts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent
ROOT_DIR = SIM_DIR.parent
DATA_DIR = ROOT_DIR / "result"
CSV_SUBDIR = "csv"


def csv_dir(out_dir: Path) -> Path:
    return out_dir / CSV_SUBDIR


COLORS = {
    "d4": "#e74c3c",
    "d6": "#8b4513",
    "d8": "#2ecc71",
    "d10": "#9b59b6",
    "d12": "#f39c12",
    "d20": "#3498db",
}

MARKERS = {
    "d4": "o",
    "d6": "s",
    "d8": "^",
    "d10": "D",
    "d12": "*",
    "d20": "v",
}


def exe_path(name: str) -> Path:
    return SIM_DIR / "bin" / f"{name}.exe"


def resolve_out_dir(out_dir: Path | None) -> Path:
    """Resolve output directory (new timestamp folder unless --out-dir is given)."""
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = DATA_DIR / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_go(parts: tuple[str, ...] = ("part1",)) -> None:
    SIM_DIR.joinpath("bin").mkdir(parents=True, exist_ok=True)
    for part in parts:
        out = SIM_DIR / "bin" / f"{part}.exe"
        cmd = ["go", "build", "-o", str(out), f"./sim/{part}"]
        print(f"[build] {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=str(ROOT_DIR))
        if proc.returncode != 0:
            sys.exit(proc.returncode)


def run_go(exe: str, args: list[str], *, stream_progress: bool = False) -> None:
    cmd = [str(exe_path(exe)), *args]
    if not exe_path(exe).exists():
        print(f"エラー: {exe_path(exe)} が見つかりません。")
        sys.exit(1)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(SIM_DIR),
        bufsize=1,
    )
    assert proc.stdout is not None
    prev_progress = False
    for raw in proc.stdout:
        line = raw.rstrip("\n").rstrip("\r")
        if stream_progress and line.startswith("PROGRESS"):
            if line.startswith("PROGRESS1:"):
                tag = "[パス1]"
                body = line.split(":", 1)[1].strip()
            elif line.startswith("PROGRESS2"):
                tag = "[パス2]"
                body = line.split(":", 1)[1].strip()
            elif line.startswith("PROGRESS3:"):
                tag = "[Part3]"
                body = line.split(":", 1)[1].strip()
            elif line.startswith("PROGRESS4:"):
                tag = "[Part4]"
                body = line.split(":", 1)[1].strip()
            else:
                tag = "[sim]"
                body = line.split(":", 1)[1].strip() if ":" in line else line
            print(f"\r    {tag} {body}    ", end="", flush=True)
            prev_progress = True
        else:
            if prev_progress:
                print()
                prev_progress = False
            print(f"    {line}", flush=True)
    if prev_progress:
        print()
    proc.wait()
    if proc.returncode != 0:
        print(f"エラー: {exe} が終了コード {proc.returncode} で終了しました。")
        sys.exit(proc.returncode)


def part_main(
    *,
    part_label: str,
    go_part: str,
    description: str,
    default_trials: int,
    plot_fn: Callable[[Path], None],
    run_sim_fn: Callable[[Path, int, int], None],
) -> None:
    p = argparse.ArgumentParser(description=description)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="output dir (default: result/<timestamp> at project root)",
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=default_trials)
    args = p.parse_args()

    out_dir = resolve_out_dir(args.out_dir)

    print(f"出力: {out_dir}")

    build_go((go_part,))
    print(f"[{part_label}] Go シム実行中...")
    run_sim_fn(out_dir, args.seed, args.trials)
    print(f"[{part_label}] グラフ生成中...")
    plot_fn(out_dir)
