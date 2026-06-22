"""Part5: basic4 pool average sim + plot."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import csv_dir, part_main, run_go  # noqa: E402
from plotting import (  # noqa: E402
    AxisSpec,
    LineChartSpec,
    LineSeries,
    PointAnnotation,
    VSpanOverlay,
    require_csv,
    save_line_chart,
)


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part5",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def plot(out_dir: Path) -> None:
    csv_path = csv_dir(out_dir) / "basic4_pool_avg.csv"
    require_csv(csv_path)

    ns, avgs, p50s, p90s, p99s = [], [], [], [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ns.append(int(row["n_extra"]))
            avgs.append(float(row["avg"]))
            p50s.append(int(row["p50"]))
            p90s.append(int(row["p90"]))
            p99s.append(int(row["p99"]))

    save_line_chart(
        LineChartSpec(
            series=[
                LineSeries(
                    x=ns,
                    y=avgs,
                    label="平均",
                    color="#e74c3c",
                    marker="o",
                    markersize=6,
                    linewidth=2,
                    annotations=[
                        PointAnnotation(text=f"{y:.1f}", color="#e74c3c")
                        for y in avgs
                    ],
                ),
                LineSeries(x=ns, y=p50s, label="p50", color="#f39c12", marker="s", linestyle="--", linewidth=1.5),
                LineSeries(x=ns, y=p90s, label="p90", color="#2ecc71", marker="^", linestyle=":", linewidth=1.5),
                LineSeries(x=ns, y=p99s, label="p99", color="#3498db", marker="D", linestyle="-.", linewidth=1.5),
            ],
            axis=AxisSpec(
                xlabel="追加ダイス数 (N)",
                ylabel="総達成値",
                title="1d10 + N × ランダム基本4",
                x_major="integer",
                y_major=5,
            ),
            figsize=(11, 6),
            legend_loc="upper left",
        ),
        out_dir / "basic4_pool_avg.png",
        vspans=[VSpanOverlay(xmin=2, xmax=3, label="序盤想定範囲 (2〜3個)")],
    )


def main() -> None:
    part_main(
        part_label="Part5",
        go_part="part5",
        description="Part5 sim + plot",
        default_trials=50000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
