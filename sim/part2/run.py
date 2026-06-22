"""Part2: marginal contribution enumeration + line chart."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import COLORS, MARKERS, csv_dir, part_main, run_go  # noqa: E402
from plotting import AxisSpec, LineChartSpec, LineSeries, read_matrix_csv, require_csv, save_line_chart  # noqa: E402


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part2",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "marginal_by_n.csv"
    require_csv(csv_path)
    dice_names, data = read_matrix_csv(csv_path, "n_others")

    save_line_chart(
        LineChartSpec(
            series=[
                LineSeries(
                    x=data[name]["x"],
                    y=data[name]["y"],
                    label=name,
                    color=COLORS.get(name, "#ffffff"),
                    marker=MARKERS.get(name, "o"),
                )
                for name in dice_names
            ],
            axis=AxisSpec(
                xlabel="他ダイス数 (n_others)",
                ylabel="限界貢献度（平均）",
                title="限界貢献度（ダイス種別 × 他ダイス数）",
                x_major="integer",
            ),
            figsize=(10, 6),
            legend_loc="lower right",
            legend_fontsize=12,
        ),
        out_dir / "marginal_by_n.png",
    )


def main() -> None:
    part_main(
        part_label="Part2",
        go_part="part2",
        description="Part2 sim + plot",
        default_trials=5000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
