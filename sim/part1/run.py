"""Part1: single-die reference table + bar chart."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import (  # noqa: E402
    BG_COLOR,
    COLORS,
    apply_dark_style,
    build_go,
    resolve_out_dir,
    run_go,
    csv_dir,
)


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go("part1", ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)])


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "part1_reference.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} がありません。")
        sys.exit(1)

    names, avgs = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names.append(row["dice"])
            avgs.append(float(row["avg_per_die"]))

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG_COLOR)
    colors = [COLORS.get(n, "#ffffff") for n in names]
    bars = ax.bar(names, avgs, color=colors, alpha=0.85)
    for bar, val in zip(bars, avgs):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.05,
            f"{val:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#eeeeee",
        )
    ax.set_ylabel("Average achievement per die", fontsize=12)
    ax.set_title("Part1: Single Die x5 Reference (avg/die)", fontsize=14)
    apply_dark_style(ax)
    fig.tight_layout()
    out_png = out_dir / "part1_reference.png"
    fig.savefig(out_png, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_png.name}")


def main() -> None:
    p = argparse.ArgumentParser(description="Part1 sim + plot")
    p.add_argument("--out-dir", type=Path, default=None, help="output dir (default: data/<timestamp>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=20000)
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
        build_go(("part1",))
        print("[Part1] Go シム実行中...")
        run_sim(out_dir, args.seed, args.trials)
    print("[Part1] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
