"""Part5: basic4 pool average sim + plot."""

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


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part5",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "basic4_pool_avg.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} がありません。")
        sys.exit(1)

    ns, avgs, p50s, p90s, p99s = [], [], [], [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n_extra"]))
            avgs.append(float(row["avg"]))
            p50s.append(int(row["p50"]))
            p90s.append(int(row["p90"]))
            p99s.append(int(row["p99"]))

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG_COLOR)
    apply_dark_style(ax)
    ax.plot(ns, avgs, color="#e74c3c", marker="o", markersize=6, linewidth=2, label="avg (平均)")
    ax.plot(ns, p50s, color="#f39c12", marker="s", markersize=5, linewidth=1.5, linestyle="--", label="p50")
    ax.plot(ns, p90s, color="#2ecc71", marker="^", markersize=5, linewidth=1.5, linestyle=":", label="p90")
    ax.plot(ns, p99s, color="#3498db", marker="D", markersize=5, linewidth=1.5, linestyle="-.", label="p99")
    for x, y in zip(ns, avgs):
        ax.annotate(
            f"{y:.1f}",
            xy=(x, y),
            xytext=(0, 8),
            textcoords="offset points",
            fontsize=9,
            color="#e74c3c",
            ha="center",
            va="bottom",
        )
    ax.axvspan(2, 3, alpha=0.08, color="#ffffff", label="序盤想定範囲 (2〜3個)")
    ax.set_xlabel("Number of extra dice (N)", fontsize=13)
    ax.set_ylabel("Total achievement value", fontsize=13)
    ax.set_title("1d10 + N × Random Basic-4 Dice", fontsize=14)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.legend(fontsize=11, loc="upper left", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_png = out_dir / "basic4_pool_avg.png"
    fig.savefig(out_png, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_png.name}")


def main() -> None:
    p = argparse.ArgumentParser(description="Part5 sim + plot")
    p.add_argument("--out-dir", type=Path, default=None, help="output dir (default: data/<timestamp>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=50000)
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
        build_go(("part5",))
        print("[Part5] Go シム実行中...")
        run_sim(out_dir, args.seed, args.trials)
    print("[Part5] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
