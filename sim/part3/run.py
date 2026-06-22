"""Part3: difficulty table sim + plot."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import csv_dir, part_main, run_go  # noqa: E402
from plotting import (  # noqa: E402
    AxisSpec,
    HLineOverlay,
    LineChartSpec,
    LineSeries,
    read_matrix_csv,
    require_csv,
    save_line_chart,
)

DIFF_LEVELS = [
    ("易(85%)", 85, "#44ff44"),
    ("普通(70%)", 70, "#ffff44"),
    ("難(55%)", 55, "#ffaa22"),
    ("超難(30%)", 30, "#ff4444"),
    ("ほぼ不可能(3%)", 3, "#ff00ff"),
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
    require_csv(csv_path)
    dice_names, data = read_matrix_csv(csv_path, "target")

    save_line_chart(
        LineChartSpec(
            series=[
                LineSeries(
                    x=data[name]["x"],
                    y=[y * 100.0 for y in data[name]["y"]],
                    label=name,
                    color=COMBO_COLORS.get(name, "#ffffff"),
                    marker=COMBO_MARKERS.get(name, "o"),
                    markersize=4,
                )
                for name in dice_names
            ],
            axis=AxisSpec(
                xlabel="目標値",
                ylabel="成功率 (%)",
                title="難易度表: 目標値別成功率\n(1d10 + 属性ダイス1個)",
                xlim=(1, 27),
                ylim=(-2, 103),
                x_major=1,
                y_major=10,
            ),
            figsize=(13, 7),
            legend_loc="lower right",
        ),
        out_dir / "difficulty_table.png",
        hlines=[
            HLineOverlay(y=pct, color=col, label=label, label_x=25.2)
            for label, pct, col in DIFF_LEVELS
        ],
    )


def main() -> None:
    part_main(
        part_label="Part3",
        go_part="part3",
        description="Part3 sim + plot",
        default_trials=100000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
