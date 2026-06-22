"""Part3: difficulty table sim + plot."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import (  # noqa: E402
    BG_COLOR,
    apply_dark_style,
    build_go,
    resolve_out_dir,
    run_go,
    csv_dir,
)

DIFF_LEVELS = [
    ("Easy(85%)", 85, "#44ff44"),
    ("Normal(70%)", 70, "#ffff44"),
    ("Hard(55%)", 55, "#ffaa22"),
    ("Very Hard(30%)", 30, "#ff4444"),
    ("Near Impossible(3%)", 3, "#ff00ff"),
]
COMBO_COLORS = {
    "d10only": "#9b59b6",
    "d10+d4(Fire)": "#e74c3c",
    "d10+d6(Earth)": "#8b4513",
    "d10+d8(Wind)": "#2ecc71",
    "d10+d20(Water)": "#3498db",
}
COMBO_MARKERS = {
    "d10only": "D",
    "d10+d4(Fire)": "o",
    "d10+d6(Earth)": "s",
    "d10+d8(Wind)": "^",
    "d10+d20(Water)": "v",
}


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part3",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "difficulty_table.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} がありません。")
        sys.exit(1)

    dice_names: list[str] = []
    data: dict[str, dict[str, list]] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        dice_names = [c for c in reader.fieldnames if c != "target"]
        for name in dice_names:
            data[name] = {"x": [], "y": []}
        for row in reader:
            tgt = int(row["target"])
            for name in dice_names:
                val = row[name].strip()
                if val:
                    data[name]["x"].append(tgt)
                    data[name]["y"].append(float(val) * 100.0)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG_COLOR)
    apply_dark_style(ax)
    for name in dice_names:
        ax.plot(
            data[name]["x"],
            data[name]["y"],
            label=name,
            color=COMBO_COLORS.get(name, "#ffffff"),
            marker=COMBO_MARKERS.get(name, "o"),
            markersize=4,
            linewidth=2,
        )
    for label, pct, col in DIFF_LEVELS:
        ax.axhline(y=pct, color=col, linestyle="--", linewidth=1.0, alpha=0.6)
        ax.text(25.2, pct, label, color=col, fontsize=8.5, va="center", ha="left")
    ax.set_xlabel("Target value", fontsize=13)
    ax.set_ylabel("Success rate (%)", fontsize=13)
    ax.set_title("Difficulty Table: Success Rate by Target\n(1d10 + 1 Elemental Die)", fontsize=14)
    ax.set_xlim(1, 27)
    ax.set_ylim(-2, 103)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.legend(fontsize=11, loc="lower right", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_png = out_dir / "difficulty_table.png"
    fig.savefig(out_png, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_png.name}")


def main() -> None:
    p = argparse.ArgumentParser(description="Part3 sim + plot")
    p.add_argument("--out-dir", type=Path, default=None, help="output dir (default: data/<timestamp>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=100000)
    p.add_argument("--plot-only", action="store_true")
    args = p.parse_args()

    if args.out_dir is not None:
        out_dir = resolve_out_dir(args.out_dir, create=True)
    elif args.plot_only:
        out_dir = resolve_out_dir(None, create=False)
    else:
        out_dir = resolve_out_dir(None, create=True)

    print(f"出力: {out_dir}")

    if not args.plot_only:
        build_go(("part3",))
        print("[Part3] Go シム実行中...")
        run_sim(out_dir, args.seed, args.trials)
    print("[Part3] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
