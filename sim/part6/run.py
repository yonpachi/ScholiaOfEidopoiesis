"""Part6: quality progression sim + plot."""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import csv_dir, part_main, run_go  # noqa: E402
from plotting import (  # noqa: E402
    AxisSpec,
    LineChartSpec,
    LineSeries,
    require_csv,
    save_line_chart,
)


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part6",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "quality_progression.csv"
    require_csv(csv_path)

    by_n: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"attempt": [], "p50": [], "p90": [], "p99": []}
    )
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = int(row["n_extra"])
            by_n[n]["attempt"].append(int(row["attempt"]))
            by_n[n]["p50"].append(int(row["p50"]))
            by_n[n]["p90"].append(int(row["p90"]))
            by_n[n]["p99"].append(int(row["p99"]))

    for n in range(1, 13):
        data = by_n[n]
        attempts = data["attempt"]
        save_line_chart(
            LineChartSpec(
                series=[
                    LineSeries(
                        x=attempts,
                        y=data["p50"],
                        label="p50",
                        color="#f39c12",
                        marker="s",
                        linestyle="--",
                        linewidth=1.5,
                    ),
                    LineSeries(
                        x=attempts,
                        y=data["p90"],
                        label="p90",
                        color="#2ecc71",
                        marker="^",
                        linestyle=":",
                        linewidth=1.5,
                    ),
                    LineSeries(
                        x=attempts,
                        y=data["p99"],
                        label="p99",
                        color="#3498db",
                        marker="D",
                        linestyle="-.",
                        linewidth=1.5,
                    ),
                ],
                axis=AxisSpec(
                    xlabel="錬金回数",
                    ylabel="品質",
                    title=f"品質成長（マナ{n} / 1d10+基本4×{n}）",
                    x_major="integer",
                    y_major=5,
                ),
                figsize=(11, 6),
                legend_loc="upper left",
            ),
            out_dir / f"quality_progression_n{n:02d}.png",
        )


def main() -> None:
    part_main(
        part_label="Part6",
        go_part="part6",
        description="Part6 quality progression sim + plot",
        default_trials=50000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
