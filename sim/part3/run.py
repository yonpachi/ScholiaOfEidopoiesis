"""Part3: race average score sim + 8-line plot."""

from __future__ import annotations

import csv
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

RACE_COLORS = {
    "Baseline": "#888888",
    "Hume": "#ffffff",
    "Makina": "#f39c12",
    "Bestia": "#e74c3c",
    "Homunculus": "#2ecc71",
    "Relicia": "#d966ff",
    "Umbra": "#ffff66",
    "RaceMean": "#cccccc",
}
RACE_MARKERS = {
    "Baseline": "x",
    "Hume": "o",
    "Makina": "D",
    "Bestia": "^",
    "Homunculus": "s",
    "Relicia": "P",
    "Umbra": "*",
    "RaceMean": "h",
}
LINE_ORDER = [
    "Baseline",
    "Hume",
    "Makina",
    "Bestia",
    "Homunculus",
    "Relicia",
    "Umbra",
    "RaceMean",
]
PCT_LINE_ORDER = [
    "Baseline",
    "Hume",
    "Makina",
    "Bestia",
    "Homunculus",
    "Relicia",
    "Umbra",
]
LINE_WIDTH = {
    "Baseline": 1.5,
    "RaceMean": 2.5,
}
LINE_STYLE = {
    "Baseline": "--",
    "RaceMean": "-",
}


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part3",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def pct_vs_race_mean(data: dict[str, dict[str, list]]) -> dict[str, dict[str, list]]:
    """Convert absolute scores to % deviation from RaceMean (RaceMean => 0%)."""
    ref = data["RaceMean"]
    ref_map = dict(zip(ref["x"], ref["y"]))
    out: dict[str, dict[str, list]] = {}
    for nm in PCT_LINE_ORDER:
        if nm not in data:
            continue
        xs, ys = [], []
        for x, y in zip(data[nm]["x"], data[nm]["y"]):
            base = ref_map.get(x)
            if base is None or base == 0:
                continue
            xs.append(x)
            ys.append((y / base - 1.0) * 100.0)
        out[nm] = {"x": xs, "y": ys}
    return out


def write_pct_csv(path: Path, pct_data: dict[str, dict[str, list]]) -> None:
    xs = sorted({x for series in pct_data.values() for x in series["x"]})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n_pool", *PCT_LINE_ORDER])
        for x in xs:
            row = [x]
            for nm in PCT_LINE_ORDER:
                val_map = dict(zip(pct_data[nm]["x"], pct_data[nm]["y"]))
                row.append(f"{val_map[x]:.4f}" if x in val_map else "")
            w.writerow(row)


def _build_series(
    data: dict[str, dict[str, list]],
    names: list[str],
) -> list[LineSeries]:
    series = []
    for nm in names:
        if nm not in data:
            continue
        series.append(
            LineSeries(
                x=data[nm]["x"],
                y=data[nm]["y"],
                label=nm,
                color=RACE_COLORS.get(nm, "#ffffff"),
                marker=RACE_MARKERS.get(nm, "o"),
                linewidth=LINE_WIDTH.get(nm, 1.8),
                linestyle=LINE_STYLE.get(nm, "-"),
            )
        )
    return series


def plot(out_dir: Path) -> None:
    score_csv = csv_dir(out_dir) / "race_score_by_n.csv"
    require_csv(score_csv)

    _, data = read_matrix_csv(score_csv, "n_pool")

    save_line_chart(
        LineChartSpec(
            series=_build_series(data, LINE_ORDER),
            axis=AxisSpec(
                xlabel="プール内総ダイス数 (n_pool)",
                ylabel="平均達成値",
                title=(
                    "種族別平均スコア — レシピプール（1d10 + d4/d6/d8/d20）\n"
                    "（種族なし / 6種族 / 試行内6種族平均）"
                ),
                x_major="integer",
            ),
            figsize=(14, 7),
            legend_loc="upper left",
        ),
        out_dir / "race_score_by_n.png",
    )

    pct_data = pct_vs_race_mean(data)
    pct_csv = csv_dir(out_dir) / "race_score_pct_by_n.csv"
    write_pct_csv(pct_csv, pct_data)

    save_line_chart(
        LineChartSpec(
            series=_build_series(pct_data, PCT_LINE_ORDER),
            axis=AxisSpec(
                xlabel="プール内総ダイス数 (n_pool)",
                ylabel="種族平均比 (%)",
                title=(
                    "種族別スコア — 6種族平均比（0% = 試行内6種族平均）\n"
                    "レシピプール（1d10 + d4/d6/d8/d20）"
                ),
                x_major="integer",
            ),
            figsize=(14, 7),
            legend_loc="upper left",
        ),
        out_dir / "race_score_pct_by_n.png",
        hlines=[
            HLineOverlay(
                y=0,
                color="#cccccc",
                linestyle="-",
                linewidth=1.2,
                alpha=0.9,
                label="種族平均 (0%)",
            )
        ],
    )


def main() -> None:
    part_main(
        part_label="Part3",
        go_part="part3",
        description="Part3: race average score sim + plot",
        default_trials=10000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
