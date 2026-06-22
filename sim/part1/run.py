"""Part1: single-die reference table + bar chart."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import COLORS, csv_dir, part_main, run_go  # noqa: E402
from plotting import AxisSpec, BarChartSpec, require_csv, save_bar_chart  # noqa: E402


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go("part1", ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)])


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "part1_reference.csv"
    require_csv(csv_path)

    names, avgs = [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            names.append(row["dice"])
            avgs.append(float(row["avg_per_die"]))

    save_bar_chart(
        BarChartSpec(
            categories=names,
            values=avgs,
            colors=[COLORS.get(n, "#ffffff") for n in names],
            value_labels=[f"{v:.2f}" for v in avgs],
            axis=AxisSpec(
                xlabel="",
                ylabel="ダイス1個あたり平均達成値",
                title="Part1: 単一ダイス×5 参照",
            ),
            figsize=(9, 5),
            value_label_offset=0.05,
        ),
        out_dir / "part1_reference.png",
    )


def main() -> None:
    part_main(
        part_label="Part1",
        go_part="part1",
        description="Part1 sim + plot",
        default_trials=20000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
