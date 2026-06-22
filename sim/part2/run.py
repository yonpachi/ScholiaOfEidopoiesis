"""Part2: marginal contribution enumeration + line chart."""

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
    COLORS,
    MARKERS,
    apply_dark_style,
    build_go,
    resolve_out_dir,
    run_go,
    csv_dir,
)


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part2",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "marginal_by_n.csv"
    if not csv_path.exists():
        print(f"エラー: {csv_path} がありません。")
        sys.exit(1)

    dice_names: list[str] = []
    data: dict[str, dict[str, list]] = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        dice_names = [c for c in reader.fieldnames if c != "n_others"]
        for name in dice_names:
            data[name] = {"x": [], "y": []}
        for row in reader:
            n = int(row["n_others"])
            for name in dice_names:
                val = row[name].strip()
                if val:
                    data[name]["x"].append(n)
                    data[name]["y"].append(float(val))

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    for name in dice_names:
        ax.plot(
            data[name]["x"],
            data[name]["y"],
            label=name,
            color=COLORS.get(name),
            marker=MARKERS.get(name, "o"),
            markersize=5,
            linewidth=2,
        )
    ax.set_xlabel("Number of other dice (n_others)", fontsize=13)
    ax.set_ylabel("Marginal contribution (avg)", fontsize=13)
    ax.set_title("Marginal Contribution by Dice Type vs Other Dice Count", fontsize=15)
    ax.legend(fontsize=12, loc="lower right", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    apply_dark_style(ax)
    fig.tight_layout()
    out_png = out_dir / "marginal_by_n.png"
    fig.savefig(out_png, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_png.name}")


def main() -> None:
    p = argparse.ArgumentParser(description="Part2 sim + plot")
    p.add_argument("--out-dir", type=Path, default=None, help="output dir (default: data/<timestamp>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=5000)
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
        build_go(("part2",))
        print("[Part2] Go シム実行中...")
        run_sim(out_dir, args.seed, args.trials)
    print("[Part2] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
