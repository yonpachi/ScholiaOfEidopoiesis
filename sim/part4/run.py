"""Part4: quality vs forging attempts, and weapon grade from that meter."""

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

MANA_COLORS = {
    "マナ0": "#7f8c8d",
    "マナ1": "#5dade2",
    "マナ2": "#2ecc71",
    "マナ3": "#f1c40f",
    "マナ4": "#e67e22",
    "マナ5": "#e74c3c",
    "マナ6": "#9b59b6",
    "マナ7": "#1abc9c",
    "マナ8": "#34495e",
    "マナ9": "#fd79a8",
}
HIGHLIGHT = {"マナ2", "マナ3"}
TRASH_HP = 20.0


def run_sim(out_dir: Path, seed: int, trials: int) -> None:
    run_go(
        "part4",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def _mana_series(data: dict[str, dict[str, list]]) -> list[LineSeries]:
    series: list[LineSeries] = []
    names = sorted(data, key=lambda n: int(n.replace("マナ", "")))
    for name in names:
        highlight = name in HIGHLIGHT
        series.append(
            LineSeries(
                x=data[name]["x"],
                y=data[name]["y"],
                label=name,
                color=MANA_COLORS.get(name, "#ffffff"),
                marker="o" if highlight else ".",
                linewidth=2.6 if highlight else 1.4,
                markersize=6 if highlight else 4,
                alpha=1.0 if highlight else 0.75,
            )
        )
    return series


def _line(
    path: Path,
    ylabel: str,
    title: str,
    png: Path,
    *,
    trash_line: bool = False,
    ylim: tuple[float, float] | None = None,
) -> None:
    require_csv(path)
    _, data = read_matrix_csv(path, "k")
    hlines: list[HLineOverlay] = []
    if trash_line:
        hlines.append(
            HLineOverlay(
                y=TRASH_HP,
                color="#e74c3c",
                linestyle="--",
                linewidth=1.4,
                alpha=0.9,
                label="初期並雑魚 HP 20",
                label_x=1.15,
            )
        )
    save_line_chart(
        LineChartSpec(
            series=_mana_series(data),
            axis=AxisSpec(
                xlabel="再錬金回数 k（最良を採用）",
                ylabel=ylabel,
                title=title,
                x_major="integer",
                ylim=ylim,
            ),
            figsize=(12, 6),
            legend_loc="upper left",
            legend_fontsize=9,
        ),
        png,
        hlines=hlines,
    )


def plot(out_dir: Path) -> None:
    csvs = csv_dir(out_dir)

    _line(
        csvs / "quality_p50_by_k.csv",
        "最良品質（p50）",
        "Part4: 再錬金回数と最良品質（中央値）\n同一レシピを k 回錬金し最良を採用（構成は均等）",
        out_dir / "quality_p50_by_k.png",
        trash_line=True,
    )
    _line(
        csvs / "quality_avg_by_k.csv",
        "最良品質（平均）",
        "Part4: 再錬金回数と最良品質（平均）\n同一レシピを k 回錬金し最良を採用（構成は均等）",
        out_dir / "quality_avg_by_k.png",
        trash_line=True,
    )
    _line(
        csvs / "quality_p99_by_k.csv",
        "最良品質（p99）",
        "Part4: 再錬金回数と最良品質（p99）",
        out_dir / "quality_p99_by_k.png",
        trash_line=True,
    )
    _line(
        csvs / "quality_reach_by_k.csv",
        "P(最良 >= 20)",
        "Part4: 再錬金回数と並雑魚一撃率\n同一レシピを k 回錬金し、最良品の品質が 20 以上",
        out_dir / "quality_reach_by_k.png",
        ylim=(0.0, 1.05),
    )

    grade_path = csvs / "weapon_grade.csv"
    require_csv(grade_path)
    grades: list[str] = []
    hits: list[float] = []
    labels: list[str] = []
    colors: list[str] = []
    with open(grade_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g = int(row["等級"])
            hit = float(row["1撃_Q2k1"])
            n_hits = row["雑魚撃数_Q2k1"]
            grades.append(str(g))
            hits.append(hit)
            labels.append(f"{int(hit)}/{n_hits}撃")
            colors.append("#2ecc71" if 9 <= g <= 12 else "#3498db")
    save_bar_chart(
        BarChartSpec(
            categories=grades,
            values=hits,
            colors=colors,
            value_labels=labels,
            axis=AxisSpec(
                xlabel="等級（小さいほど強い）",
                ylabel="中量中の1撃（2マナ・未鍛錬 p50）",
                title="Part4: 武器等級 → 中量中1撃 / 並雑魚への手数\n品質は動かさない。割る側（等級）で武器を合わせる",
            ),
            figsize=(14, 6),
            value_label_fontsize=8,
        ),
        out_dir / "weapon_grade_hit.png",
    )


def main() -> None:
    part_main(
        part_label="Part4",
        go_part="part4",
        description="Part4: quality vs forging attempts + weapon grade",
        default_trials=5000,
        plot_fn=plot,
        run_sim_fn=run_sim,
    )


if __name__ == "__main__":
    main()
