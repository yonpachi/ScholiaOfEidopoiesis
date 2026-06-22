"""Shared helpers for sim/partN run.py scripts."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT_DIR = Path(__file__).resolve().parent.parent
SIM_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
CSV_SUBDIR = "csv"
FONTS_DIR = SIM_DIR / "fonts"

# Prefer bundled Noto, then common OS Japanese fonts (Windows / macOS / Linux).
JP_FONT_CANDIDATES = (
    "Noto Sans JP",
    "Noto Sans CJK JP",
    "Yu Gothic",
    "Yu Gothic UI",
    "Meiryo",
    "MS Gothic",
    "Hiragino Sans",
    "Hiragino Kaku Gothic ProN",
    "IPAGothic",
    "TakaoGothic",
    "Source Han Sans JP",
)


def configure_plot_fonts() -> str | None:
    """Use a CJK-capable sans font so Japanese labels render without glyph warnings."""
    bundled = (
        FONTS_DIR / "NotoSansJP-Regular.otf",
        FONTS_DIR / "NotoSansJP-Regular.ttf",
        FONTS_DIR / "NotoSansCJKjp-Regular.otf",
    )
    for path in bundled:
        if path.is_file():
            font_manager.fontManager.addfont(str(path))
            break

    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((name for name in JP_FONT_CANDIDATES if name in available), None)
    if chosen is None:
        return None

    sans = [chosen, "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = sans
    # Avoid minus signs rendering as tofu with Japanese fonts.
    plt.rcParams["axes.unicode_minus"] = False
    return chosen


configure_plot_fonts()


def csv_dir(out_dir: Path) -> Path:
    return out_dir / CSV_SUBDIR


COLORS = {
    "d4": "#e74c3c",
    "d6": "#8b4513",
    "d8": "#2ecc71",
    "d10": "#9b59b6",
    "d20": "#3498db",
    "d12": "#f39c12",
}

MARKERS = {
    "d4": "o",
    "d6": "s",
    "d8": "^",
    "d10": "D",
    "d20": "v",
    "d12": "*",
}

BG_COLOR = "#0f0f1a"


def apply_dark_style(ax) -> None:
    ax.set_facecolor("#1a1a2e")
    ax.grid(True, linestyle="--", alpha=0.3, color="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555555")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#eeeeee")


def exe_path(name: str) -> Path:
    return SIM_DIR / "bin" / f"{name}.exe"


def find_latest_data_dir() -> Path | None:
    if not DATA_DIR.is_dir():
        return None
    dirs = [p for p in DATA_DIR.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.name)


def resolve_out_dir(out_dir: Path | None, *, create: bool) -> Path:
    """Resolve output directory. create=True → new timestamp folder; False → latest existing."""
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir
    if create:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        d = DATA_DIR / ts
        d.mkdir(parents=True, exist_ok=True)
        return d
    latest = find_latest_data_dir()
    if latest is None:
        print(f"エラー: {DATA_DIR} に出力フォルダがありません。Part1/2 を先に実行してください。")
        sys.exit(1)
    return latest


def build_go(parts: tuple[str, ...] = ("part1", "part2", "part3", "part4", "part5")) -> None:
    for part in parts:
        cmd = ["go", "build", "-o", f"bin/{part}.exe", f"./{part}"]
        print(f"[build] {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=str(SIM_DIR))
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
        if stream_progress and line.startswith(("PROGRESS1:", "PROGRESS2:", "PROGRESS3:", "PROGRESS4:", "PROGRESS5:")):
            if line.startswith("PROGRESS1:"):
                tag = "[パス1]"
            elif line.startswith("PROGRESS2:"):
                tag = "[パス2]"
            elif line.startswith("PROGRESS3:"):
                tag = "[Part3]"
            elif line.startswith("PROGRESS4:"):
                tag = "[Part4]"
            else:
                tag = "[Part5]"
            body = line.split(":", 1)[1].strip()
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
