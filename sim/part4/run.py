"""Part4: race ability comparison sim + plot."""

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

RACE_COLORS = {
    "Hume": "#ffffff",
    "Makina": "#f39c12",
    "Bestia": "#e74c3c",
    "Homunculus": "#2ecc71",
    "Relicia": "#d966ff",
    "Umbra": "#ffff66",
}
RACE_MARKERS = {
    "Hume": "o",
    "Makina": "D",
    "Bestia": "^",
    "Homunculus": "s",
    "Relicia": "P",
    "Umbra": "*",
}


def read_race_csv(path: Path):
    names, data = [], {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        names = [c for c in reader.fieldnames if c != "n_pool"]
        for nm in names:
            data[nm] = {"x": [], "y": []}
        for row in reader:
            n = int(row["n_pool"])
            for nm in names:
                v = row.get(nm, "").strip()
                if v:
                    data[nm]["x"].append(n)
                    data[nm]["y"].append(float(v))
    return names, data


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part4",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    race_csv = csv_dir(out_dir) / "race_ability_by_n.csv"
    if not race_csv.exists():
        print(f"エラー: {race_csv} がありません。")
        sys.exit(1)

    use_rate_csv = csv_dir(out_dir) / "race_use_rate_by_n.csv"
    delta_use_csv = csv_dir(out_dir) / "race_delta_use_by_n.csv"
    homo_csv = csv_dir(out_dir) / "homunculus_option_distribution.csv"

    race_names, avg_data = read_race_csv(race_csv)
    has_ur = use_rate_csv.exists()
    has_du = delta_use_csv.exists()
    ur_data = read_race_csv(use_rate_csv)[1] if has_ur else {}
    du_data = read_race_csv(delta_use_csv)[1] if has_du else {}

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG_COLOR)
    apply_dark_style(ax)
    for nm in race_names:
        xs = avg_data[nm]["x"]
        ys = avg_data[nm]["y"]
        color = RACE_COLORS.get(nm, "#ffffff")
        ax.plot(xs, ys, label=nm, color=color, marker=RACE_MARKERS.get(nm, "o"), markersize=5, linewidth=2)
        if has_ur and has_du and nm in ur_data and nm in du_data:
            ur_map = dict(zip(ur_data[nm]["x"], ur_data[nm]["y"]))
            du_map = dict(zip(du_data[nm]["x"], du_data[nm]["y"]))
            for i, (x, y) in enumerate(zip(xs, ys)):
                ur = ur_map.get(x)
                du = du_map.get(x)
                if ur is None or du is None:
                    continue
                va = "bottom" if i % 2 == 0 else "top"
                yoff = 5 if i % 2 == 0 else -5
                ax.annotate(
                    f"u:{ur * 100:.0f}% d:{du:.1f}",
                    xy=(x, y),
                    xytext=(0, yoff),
                    textcoords="offset points",
                    fontsize=5,
                    color=color,
                    alpha=0.80,
                    va=va,
                    ha="center",
                )
    ax.axhline(y=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Total dice in pool (n_pool)", fontsize=13)
    ax.set_ylabel("avg delta (achievement increase)", fontsize=13)
    ax.set_title(
        "Race Ability Strength — avg delta per Pool Size\n"
        "  annotations: u = use rate,  d = avg Δ when used",
        fontsize=13,
    )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.legend(fontsize=11, loc="upper left", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_png = out_dir / "race_ability_by_n.png"
    fig.savefig(out_png, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_png.name}")

    if homo_csv.exists():
        homo_labels, homo_rates, homo_counts = [], [], []
        with open(homo_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                homo_labels.append(row["option"])
                homo_counts.append(int(row["count"]))
                homo_rates.append(float(row["rate"]) * 100.0)
        fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG_COLOR)
        apply_dark_style(ax)
        bar_colors = ["#2ecc71", "#e74c3c", "#3498db"]
        bars = ax.bar(homo_labels, homo_rates, color=bar_colors[: len(homo_labels)], alpha=0.85)
        for bar, rate, count in zip(bars, homo_rates, homo_counts):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{rate:.1f}%\n(n={count:,})",
                ha="center",
                va="bottom",
                fontsize=10,
                color="#eeeeee",
            )
        ax.set_ylabel("Selection rate (%)", fontsize=12)
        ax.set_title("Homunculus Option Selection Distribution", fontsize=13)
        ax.set_ylim(0, max(homo_rates) * 1.25 if homo_rates else 100)
        fig.tight_layout()
        out_homo = out_dir / "homunculus_options.png"
        fig.savefig(out_homo, dpi=150, facecolor=BG_COLOR)
        plt.close(fig)
        print(f"    出力: {out_homo.name}")


def main() -> None:
    p = argparse.ArgumentParser(description="Part4 sim + plot")
    p.add_argument("--out-dir", type=Path, default=None, help="output dir (default: data/<timestamp>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=10000)
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
        build_go(("part4",))
        print("[Part4] Go シム実行中...")
        run_sim(out_dir, args.seed, args.trials)
    print("[Part4] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
