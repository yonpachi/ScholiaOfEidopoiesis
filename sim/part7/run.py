"""Part7: Part6 quality -> effective combat stats + plots."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import build_go, csv_dir, resolve_out_dir, run_go  # noqa: E402
from effective_stats import (  # noqa: E402
    ACTIONS,
    ARMOR_TABLE,
    CONSUMABLE_DEFAULT_WEIGHT,
    CONSUMABLE_GRADE,
    OPTIMAL_ACTION_INDEX,
    REFERENCE_ATTEMPT,
    WEAPON_TABLE,
    grade_for_mana,
    load_quality_progression,
    run_effective_stats,
    weapon_damage,
)
from plotting import (  # noqa: E402
    AxisSpec,
    BG_COLOR,
    LineChartSpec,
    LineSeries,
    VSpanOverlay,
    apply_dark_style,
    configure_plot_fonts,
    require_csv,
    save_line_chart,
)

configure_plot_fonts()

GRADE_BANDS = (
    (1, 3, "等級7 (~3マナ)", "#3498db"),
    (4, 6, "等級6 (4~6マナ)", "#2ecc71"),
    (7, 9, "等級5 (7~9マナ)", "#f39c12"),
    (10, 12, "等級4 (10~マナ)", "#e74c3c"),
)


def run_part6_sim(out_dir: Path, seed: int, trials: int) -> None:
    build_go(("part6",))
    print("[Part6] Go シム実行中...")
    run_go(
        "part6",
        ["-out", str(out_dir), "-seed", str(seed), "-trials", str(trials)],
        stream_progress=True,
    )


def ensure_stats(out_dir: Path) -> None:
    require_csv(csv_dir(out_dir) / "quality_progression.csv")
    print("[Part7] 実効値算出中...")
    run_effective_stats(out_dir)


def plot_dpc_comparison(out_dir: Path, rows: list[dict[str, str]]) -> None:
    ns = [int(r["n_extra"]) for r in rows]
    quality_rows = {
        (r.n_extra, r.attempt): r
        for r in load_quality_progression(csv_dir(out_dir) / "quality_progression.csv")
    }

    series: list[LineSeries] = [
        LineSeries(
            x=ns,
            y=[float(r["consumable_dpc"]) for r in rows],
            label=f"消耗品（DPC=B、等級{CONSUMABLE_GRADE}）",
            color="#3498db",
            marker="s",
            linestyle="--",
            linewidth=2,
        )
    ]
    colors = {"軽量": "#2ecc71", "中量": "#e74c3c", "重量": "#f39c12"}
    action_index = 1  # 中行動 — same action band for all weapon weights
    action_label = ACTIONS[action_index]
    for weight in ("軽量", "中量", "重量"):
        dpcs: list[float] = []
        for n in ns:
            qr = quality_rows.get((n, REFERENCE_ATTEMPT))
            if qr is None:
                dpcs.append(0.0)
                continue
            grade = grade_for_mana(n)
            wait, coef = WEAPON_TABLE[weight][action_index]
            _, _, dpc = weapon_damage(qr.p50, grade, wait, coef)
            dpcs.append(dpc)
        series.append(
            LineSeries(
                x=ns,
                y=dpcs,
                label=f"武器{weight}（{action_label}）",
                color=colors[weight],
                marker="o",
                linewidth=2,
            )
        )

    save_line_chart(
        LineChartSpec(
            series=series,
            axis=AxisSpec(
                xlabel="マナ数 (n_extra)",
                ylabel="DPC（効果量÷待機値）",
                title=(
                    f"Part7: DPC比較（attempt={REFERENCE_ATTEMPT}, p50）"
                    f" — 武器種別 vs 消耗品（{action_label}）"
                ),
                x_major="integer",
            ),
            figsize=(12, 6),
            legend_loc="upper left",
        ),
        out_dir / "part7-1_dpc_comparison.png",
        vspans=[
            VSpanOverlay(xmin=lo, xmax=hi, label=label, color=color, alpha=0.07)
            for lo, hi, label, color in GRADE_BANDS
        ],
    )


def _load_summary_rows(out_dir: Path, attempt: int, percentile: str) -> list[dict[str, str]]:
    path = csv_dir(out_dir) / "effective_stats_summary.csv"
    require_csv(path)
    rows: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["attempt"]) == attempt and row["percentile"] == percentile:
                rows.append(row)
    rows.sort(key=lambda r: int(r["n_extra"]))
    return rows


def plot_dpc_by_weight(out_dir: Path, rows: list[dict[str, str]]) -> None:
    ns = [int(r["n_extra"]) for r in rows]
    quality_rows = {
        (r.n_extra, r.attempt): r
        for r in load_quality_progression(csv_dir(out_dir) / "quality_progression.csv")
    }

    series: list[LineSeries] = []
    colors = {"軽量": "#3498db", "中量": "#e74c3c", "重量": "#f39c12"}
    heal_dpcs = [float(r["consumable_dpc"]) for r in rows]
    series.append(
        LineSeries(
            x=ns,
            y=heal_dpcs,
            label=f"消耗品（DPC=B、{CONSUMABLE_DEFAULT_WEIGHT}）",
            color="#3498db",
            marker="s",
            linestyle="--",
            linewidth=1.5,
        )
    )
    for weight in ("軽量", "中量", "重量"):
        dpcs: list[float] = []
        for n in ns:
            qr = quality_rows.get((n, REFERENCE_ATTEMPT))
            if qr is None:
                dpcs.append(0.0)
                continue
            q = qr.p50
            grade = grade_for_mana(n)
            idx = OPTIMAL_ACTION_INDEX[weight]
            wait, coef = WEAPON_TABLE[weight][idx]
            _, _, dpc = weapon_damage(q, grade, wait, coef)
            dpcs.append(dpc)
        opt_action = ACTIONS[OPTIMAL_ACTION_INDEX[weight]]
        series.append(
            LineSeries(
                x=ns,
                y=dpcs,
                label=f"{weight}（最適={opt_action}）",
                color=colors[weight],
                marker="o",
                linewidth=2,
            )
        )

    save_line_chart(
        LineChartSpec(
            series=series,
            axis=AxisSpec(
                xlabel="マナ数 (n_extra)",
                ylabel="DPC（ダメージ÷待機値）",
                title=f"Part7: 武器DPC・最適行動帯（attempt={REFERENCE_ATTEMPT}, p50）",
                x_major="integer",
            ),
            figsize=(12, 6),
            legend_loc="upper left",
        ),
        out_dir / "part7-2_dpc_optimal.png",
        vspans=[
            VSpanOverlay(xmin=lo, xmax=hi, label=label, color=color, alpha=0.07)
            for lo, hi, label, color in GRADE_BANDS
        ],
    )


def _load_optimal_oneshot_rows(
    out_dir: Path, attempt: int, percentile: str
) -> list[dict[str, str]]:
    path = csv_dir(out_dir) / "effective_stats_optimal_oneshot.csv"
    require_csv(path)
    rows: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["attempt"]) == attempt and row["percentile"] == percentile:
                rows.append(row)
    rows.sort(key=lambda r: int(r["n_extra"]))
    return rows


def plot_oneshot_comparison(out_dir: Path, rows: list[dict[str, str]]) -> None:
    ns = [int(r["n_extra"]) for r in rows]
    consumable = [int(r["consumable_effect"]) for r in rows]
    defense = [int(r["defense"]) for r in rows]
    colors = {"軽量": "#3498db", "中量": "#e74c3c", "重量": "#f39c12"}
    series: list[LineSeries] = [
        LineSeries(
            x=ns,
            y=consumable,
            label="消耗品（一撃効果）",
            color="#3498db",
            marker="s",
            linestyle="--",
            linewidth=1.5,
        ),
        LineSeries(
            x=ns,
            y=defense,
            label="基礎防護（防御値 B）",
            color="#9b59b6",
            marker="d",
            linestyle="-.",
            linewidth=1.5,
        ),
    ]
    for weight in ("軽量", "中量", "重量"):
        weapon_vals = [int(r[f"weapon_{weight}_best_damage"]) for r in rows]
        armor_vals = [int(r[f"armor_{weight}_best_armor"]) for r in rows]
        series.append(
            LineSeries(
                x=ns,
                y=weapon_vals,
                label=f"武器{weight}（一撃最大）",
                color=colors[weight],
                marker="o",
                linewidth=2,
            )
        )
        series.append(
            LineSeries(
                x=ns,
                y=armor_vals,
                label=f"<装甲>{weight}（一撃最大）",
                color=colors[weight],
                marker="^",
                linestyle=":",
                linewidth=1.5,
            )
        )

    save_line_chart(
        LineChartSpec(
            series=series,
            axis=AxisSpec(
                xlabel="マナ数 (n_extra)",
                ylabel="一撃値",
                title=f"Part7: 一撃値比較（attempt={REFERENCE_ATTEMPT}, p50）",
                x_major="integer",
            ),
            figsize=(12, 7),
            legend_loc="upper left",
        ),
        out_dir / "part7-4_oneshot_comparison.png",
        vspans=[
            VSpanOverlay(xmin=lo, xmax=hi, label=label, color=color, alpha=0.07)
            for lo, hi, label, color in GRADE_BANDS
        ],
    )


def plot_armor_heatmap(out_dir: Path, n_extra: int, attempt: int, percentile: str) -> None:
    path = csv_dir(out_dir) / "effective_stats_oneshot.csv"
    require_csv(path)

    dmg_grid = np.zeros((3, 4), dtype=float)
    def_grid = np.zeros((3, 4), dtype=float)
    weights = ["軽量", "中量", "重量"]
    for wi, weight in enumerate(weights):
        for ai, action in enumerate(ACTIONS):
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if (
                        int(row["n_extra"]) == n_extra
                        and int(row["attempt"]) == attempt
                        and row["percentile"] == percentile
                        and row["kind"] == "armor"
                        and row["weight"] == weight
                        and row["action"] == action
                    ):
                        dmg_grid[wi, ai] = float(row["oneshot_value"])
                        def_grid[wi, ai] = float(row["defense"])
                        break

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
    apply_dark_style(ax)
    im = ax.imshow(dmg_grid, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(4), labels=ACTIONS)
    ax.set_yticks(range(3), labels=weights)
    ax.set_title(
        f"Part7: 防具 `<装甲>` + 防御値（マナ{n_extra}, attempt={attempt}, {percentile}）",
        fontsize=14,
        color="#eeeeee",
    )
    for i in range(3):
        for j in range(4):
            armor_val = int(dmg_grid[i, j])
            def_val = int(def_grid[i, j])
            wait, coef = ARMOR_TABLE[weights[i]][j]
            ax.text(
                j,
                i,
                f"装甲{armor_val}\n防御{def_val}\n({wait}/{coef})",
                ha="center",
                va="center",
                color="#111111" if armor_val < dmg_grid.max() * 0.7 else "#ffffff",
                fontsize=8,
            )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#cccccc")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#cccccc")
    fig.tight_layout()
    fig.savefig(out_dir / f"part7-3_armor_heat_n{n_extra:02d}.png", dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: part7-3_armor_heat_n{n_extra:02d}.png")


def plot_weapon_heatmap(out_dir: Path, n_extra: int, attempt: int, percentile: str) -> None:
    path = csv_dir(out_dir) / "effective_stats_detail.csv"
    require_csv(path)

    grid = np.zeros((3, 4), dtype=float)
    weights = ["軽量", "中量", "重量"]
    for wi, weight in enumerate(weights):
        for ai, action in enumerate(ACTIONS):
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if (
                        int(row["n_extra"]) == n_extra
                        and int(row["attempt"]) == attempt
                        and row["percentile"] == percentile
                        and row["kind"] == "weapon"
                        and row["weight"] == weight
                        and row["action"] == action
                    ):
                        grid[wi, ai] = float(row["value"])
                        break

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
    apply_dark_style(ax)
    im = ax.imshow(grid, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(4), labels=ACTIONS)
    ax.set_yticks(range(3), labels=weights)
    ax.set_title(
        f"Part7: 武器ダメージ（マナ{n_extra}, attempt={attempt}, {percentile}）",
        fontsize=14,
        color="#eeeeee",
    )
    for i in range(3):
        for j in range(4):
            val = int(grid[i, j])
            wait, coef = WEAPON_TABLE[weights[i]][j]
            ax.text(
                j,
                i,
                f"{val}\n({wait}/{coef})",
                ha="center",
                va="center",
                color="#111111" if val < grid.max() * 0.7 else "#ffffff",
                fontsize=9,
            )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color="#cccccc")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#cccccc")
    fig.tight_layout()
    fig.savefig(out_dir / f"part7-3_weapon_heat_n{n_extra:02d}.png", dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: part7-3_weapon_heat_n{n_extra:02d}.png")


def plot(out_dir: Path) -> None:
    ensure_stats(out_dir)
    rows = _load_summary_rows(out_dir, REFERENCE_ATTEMPT, "p50")
    opt_rows = _load_optimal_oneshot_rows(out_dir, REFERENCE_ATTEMPT, "p50")
    if not rows or not opt_rows:
        print("エラー: effective_stats_summary / optimal_oneshot に参照行がありません。")
        sys.exit(1)

    plot_dpc_comparison(out_dir, rows)
    plot_dpc_by_weight(out_dir, rows)
    plot_oneshot_comparison(out_dir, opt_rows)

    for n in (3, 6, 9):
        if any(int(r["n_extra"]) == n for r in rows):
            plot_weapon_heatmap(out_dir, n, REFERENCE_ATTEMPT, "p50")
            plot_armor_heatmap(out_dir, n, REFERENCE_ATTEMPT, "p50")


def main() -> None:
    p = argparse.ArgumentParser(description="Part7: run Part6 then effective stats + plots")
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trials", type=int, default=50000, help="Part6 trials")
    p.add_argument("--plot-only", action="store_true")
    p.add_argument("--skip-part6", action="store_true", help="reuse existing quality_progression.csv")
    args = p.parse_args()

    if args.out_dir is not None:
        out_dir = resolve_out_dir(args.out_dir, create=True)
    elif args.plot_only or args.skip_part6:
        out_dir = resolve_out_dir(None, create=False)
    else:
        out_dir = resolve_out_dir(None, create=True)

    print(f"出力: {out_dir}")

    if not args.plot_only and not args.skip_part6:
        run_part6_sim(out_dir, args.seed, args.trials)
        print("[Part7] 実効値算出中...")
        run_effective_stats(out_dir)

    print("[Part7] グラフ生成中...")
    plot(out_dir)


if __name__ == "__main__":
    main()
