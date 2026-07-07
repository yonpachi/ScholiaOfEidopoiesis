"""Part2: race ability comparison sim + plot (from backup part4)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import csv_dir, part_main, run_go  # noqa: E402
from plotting import (  # noqa: E402
    AxisSpec,
    BarChartSpec,
    HLineOverlay,
    LineChartSpec,
    LineSeries,
    read_matrix_csv,
    require_csv,
    save_bar_chart,
    save_line_chart,
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

HOMO_OPTION_SERIES = (
    ("fix_rate", "修正", "#2ecc71", "o"),
    ("manifest_rate", "発現", "#e74c3c", "s"),
    ("converge_rate", "収束", "#3498db", "^"),
)
HOMO_OPTION_LABELS = {
    "fix": "修正",
    "manifest": "発現",
    "converge": "収束",
    "mutate": "収束",  # 旧 CSV 互換
}


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part2",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot_homunculus_options_by_n(out_dir: Path) -> None:
    homo_by_n_csv = csv_dir(out_dir) / "homunculus_option_by_n.csv"
    if not homo_by_n_csv.exists():
        return

    xs: list[int] = []
    rates: dict[str, list[float]] = {key: [] for key, _, _, _ in HOMO_OPTION_SERIES}
    with open(homo_by_n_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fix = float(row.get("fix_rate", 0) or 0)
            manifest = float(row.get("manifest_rate", 0) or 0)
            converge = float(row.get("converge_rate") or row.get("mutate_rate", 0) or 0)
            if fix + manifest + converge <= 0:
                continue
            xs.append(int(row["n_pool"]))
            rates["fix_rate"].append(fix * 100.0)
            rates["manifest_rate"].append(manifest * 100.0)
            rates["converge_rate"].append(converge * 100.0)

    if not xs:
        return

    save_line_chart(
        LineChartSpec(
            series=[
                LineSeries(
                    x=xs,
                    y=rates[col],
                    label=label,
                    color=color,
                    marker=marker,
                )
                for col, label, color, marker in HOMO_OPTION_SERIES
            ],
            axis=AxisSpec(
                xlabel="プール内総ダイス数 (n_pool)",
                ylabel="選択率 (%)",
                title="ホムンクルス進化 — マナ別三択選択率",
                x_major="integer",
                ylim=(0, 100),
                y_major=10,
            ),
            figsize=(12, 6),
            legend_loc="upper right",
        ),
        out_dir / "homunculus_options_by_n.png",
    )


def plot(out_dir: Path) -> None:
    race_csv = csv_dir(out_dir) / "race_ability_by_n.csv"
    require_csv(race_csv)

    use_rate_csv = csv_dir(out_dir) / "race_use_rate_by_n.csv"
    delta_use_csv = csv_dir(out_dir) / "race_delta_use_by_n.csv"
    has_ur = use_rate_csv.exists()
    has_du = delta_use_csv.exists()
    race_names, avg_data = read_matrix_csv(race_csv, "n_pool")
    ur_data = read_matrix_csv(use_rate_csv, "n_pool")[1] if has_ur else {}
    du_data = read_matrix_csv(delta_use_csv, "n_pool")[1] if has_du else {}

    def annotate_race(ax) -> None:
        if not (has_ur and has_du):
            return
        for nm in race_names:
            if nm not in ur_data or nm not in du_data:
                continue
            xs = avg_data[nm]["x"]
            ys = avg_data[nm]["y"]
            color = RACE_COLORS.get(nm, "#ffffff")
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
                    f"使用{ur * 100:.0f}% Δ{du:.1f}",
                    xy=(x, y),
                    xytext=(0, yoff),
                    textcoords="offset points",
                    fontsize=5,
                    color=color,
                    alpha=0.80,
                    va=va,
                    ha="center",
                )

    save_line_chart(
        LineChartSpec(
            series=[
                LineSeries(
                    x=avg_data[nm]["x"],
                    y=avg_data[nm]["y"],
                    label=nm,
                    color=RACE_COLORS.get(nm, "#ffffff"),
                    marker=RACE_MARKERS.get(nm, "o"),
                )
                for nm in race_names
            ],
            axis=AxisSpec(
                xlabel="プール内総ダイス数 (n_pool)",
                ylabel="平均デルタ（達成値増分）",
                title=(
                    "種族能力 — プールサイズ別平均デルタ\n"
                    "（注釈: 使用率 / 使用時平均Δ）"
                ),
                x_major="integer",
            ),
            figsize=(14, 7),
            legend_loc="upper left",
        ),
        out_dir / "race_ability_by_n.png",
        hlines=[
            HLineOverlay(y=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5)
        ],
        post_draw=annotate_race,
    )

    homo_csv = csv_dir(out_dir) / "homunculus_option_distribution.csv"
    if homo_csv.exists():
        homo_labels, homo_rates, homo_counts = [], [], []
        with open(homo_csv, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                homo_labels.append(HOMO_OPTION_LABELS.get(row["option"], row["option"]))
                homo_counts.append(int(row["count"]))
                homo_rates.append(float(row["rate"]) * 100.0)

        save_bar_chart(
            BarChartSpec(
                categories=homo_labels,
                values=homo_rates,
                colors=["#2ecc71", "#e74c3c", "#3498db"][: len(homo_labels)],
                value_labels=[
                    f"{rate:.1f}%\n(n={count:,})"
                    for rate, count in zip(homo_rates, homo_counts)
                ],
                axis=AxisSpec(
                    xlabel="",
                    ylabel="選択率 (%)",
                    title="ホムンクルス選択肢別出現率",
                    ylim=(0, max(homo_rates) * 1.25 if homo_rates else 100),
                ),
                figsize=(7, 5),
                value_label_offset=0.5,
            ),
            out_dir / "homunculus_options.png",
        )

    plot_homunculus_options_by_n(out_dir)


def main() -> None:
    part_main(
        part_label="Part2",
        go_part="part2",
        description="Part2: race ability sim + plot",
        default_trials=10000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
