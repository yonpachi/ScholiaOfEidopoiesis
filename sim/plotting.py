"""Shared matplotlib chart rendering for sim/partN run.py scripts."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager
from matplotlib.axes import Axes

SIM_DIR = Path(__file__).resolve().parent
FONTS_DIR = SIM_DIR / "fonts"

BG_COLOR = "#0f0f1a"
DEFAULT_DPI = 150
LEGEND_KWARGS = {
    "facecolor": "#2a2a3e",
    "edgecolor": "#555555",
    "labelcolor": "#eeeeee",
}

JP_FONT_CANDIDATES = (
    "Noto Sans JP",
    "Noto Sans CJK JP",
    "Yu Gothic",
    "Yu Gothic UI",
    "Meiryo",
    "MS Gothic",
    "Hiragino Sans",
    "Hiragino Kaku Gothic ProN",
    "IPAGothic",
    "TakaoGothic",
    "Source Han Sans JP",
)


def configure_plot_fonts() -> str | None:
    """Use a CJK-capable sans font so Japanese labels render without glyph warnings."""
    bundled = (
        FONTS_DIR / "NotoSansJP-Regular.otf",
        FONTS_DIR / "NotoSansJP-Regular.ttf",
        FONTS_DIR / "NotoSansCJKjp-Regular.otf",
    )
    for path in bundled:
        if path.is_file():
            font_manager.fontManager.addfont(str(path))
            break

    available = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((name for name in JP_FONT_CANDIDATES if name in available), None)
    if chosen is None:
        return None

    sans = [chosen, "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = sans
    plt.rcParams["axes.unicode_minus"] = False
    return chosen


configure_plot_fonts()


def apply_dark_style(ax: Axes) -> None:
    ax.set_facecolor("#1a1a2e")
    ax.grid(True, linestyle="--", alpha=0.3, color="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555555")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#eeeeee")


def read_matrix_csv(path: Path, row_key: str) -> tuple[list[str], dict[str, dict[str, list]]]:
    """Read a wide CSV into series dicts keyed by column name."""
    names: list[str] = []
    data: dict[str, dict[str, list]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return names, data
        names = [c for c in reader.fieldnames if c != row_key]
        for name in names:
            data[name] = {"x": [], "y": []}
        for row in reader:
            x = int(row[row_key])
            for name in names:
                val = row.get(name, "").strip()
                if val:
                    data[name]["x"].append(x)
                    data[name]["y"].append(float(val))
    return names, data


def require_csv(path: Path) -> None:
    if not path.exists():
        print(f"エラー: {path} がありません。")
        sys.exit(1)


@dataclass
class AxisSpec:
    xlabel: str
    ylabel: str
    title: str
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    x_major: Literal["integer"] | int | None = None
    y_major: int | None = None


@dataclass
class PointAnnotation:
    text: str
    color: str = "#eeeeee"
    y_offset: float = 8
    fontsize: float = 9
    alpha: float = 1.0
    va: str = "bottom"
    ha: str = "center"


@dataclass
class LineSeries:
    x: Sequence[float]
    y: Sequence[float]
    label: str
    color: str
    marker: str = "o"
    linestyle: str = "-"
    markersize: float = 5
    linewidth: float = 2
    alpha: float = 1.0
    annotations: list[PointAnnotation] | None = None


@dataclass
class LineChartSpec:
    series: list[LineSeries]
    axis: AxisSpec
    figsize: tuple[float, float] = (10, 6)
    legend_loc: str = "best"
    legend_fontsize: float = 11


@dataclass
class HLineOverlay:
    y: float
    color: str
    label: str | None = None
    label_x: float | None = None
    linestyle: str = "--"
    linewidth: float = 1.0
    alpha: float = 0.6
    label_fontsize: float = 8.5


@dataclass
class VSpanOverlay:
    xmin: float
    xmax: float
    label: str | None = None
    color: str = "#ffffff"
    alpha: float = 0.08


@dataclass
class BarChartSpec:
    categories: Sequence[str]
    values: Sequence[float]
    axis: AxisSpec
    colors: Sequence[str] | None = None
    value_labels: Sequence[str] | None = None
    figsize: tuple[float, float] = (9, 5)
    bar_alpha: float = 0.85
    value_label_fontsize: float = 10
    value_label_color: str = "#eeeeee"
    value_label_offset: float = 0.05


def _apply_axis_spec(ax: Axes, spec: AxisSpec) -> None:
    ax.set_xlabel(spec.xlabel, fontsize=13)
    ax.set_ylabel(spec.ylabel, fontsize=13)
    ax.set_title(spec.title, fontsize=14)
    if spec.xlim is not None:
        ax.set_xlim(*spec.xlim)
    if spec.ylim is not None:
        ax.set_ylim(*spec.ylim)
    if spec.x_major == "integer":
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    elif isinstance(spec.x_major, int):
        ax.xaxis.set_major_locator(ticker.MultipleLocator(spec.x_major))
    if spec.y_major is not None:
        ax.yaxis.set_major_locator(ticker.MultipleLocator(spec.y_major))


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=DEFAULT_DPI, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {path.name}")


def save_line_chart(
    spec: LineChartSpec,
    path: Path,
    *,
    hlines: Sequence[HLineOverlay] = (),
    vspans: Sequence[VSpanOverlay] = (),
    post_draw: Callable[[Axes], None] | None = None,
) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=spec.figsize, facecolor=BG_COLOR)
    apply_dark_style(ax)

    for span in vspans:
        ax.axvspan(span.xmin, span.xmax, alpha=span.alpha, color=span.color, label=span.label)

    for s in spec.series:
        ax.plot(
            s.x,
            s.y,
            label=s.label,
            color=s.color,
            marker=s.marker,
            linestyle=s.linestyle,
            markersize=s.markersize,
            linewidth=s.linewidth,
            alpha=s.alpha,
        )
        if s.annotations:
            for x, y, ann in zip(s.x, s.y, s.annotations, strict=True):
                ax.annotate(
                    ann.text,
                    xy=(x, y),
                    xytext=(0, ann.y_offset),
                    textcoords="offset points",
                    fontsize=ann.fontsize,
                    color=ann.color,
                    alpha=ann.alpha,
                    va=ann.va,
                    ha=ann.ha,
                )

    for hl in hlines:
        ax.axhline(y=hl.y, color=hl.color, linestyle=hl.linestyle, linewidth=hl.linewidth, alpha=hl.alpha)
        if hl.label is not None and hl.label_x is not None:
            ax.text(hl.label_x, hl.y, hl.label, color=hl.color, fontsize=hl.label_fontsize, va="center", ha="left")

    if post_draw is not None:
        post_draw(ax)

    _apply_axis_spec(ax, spec.axis)
    if spec.series or any(v.label for v in vspans):
        ax.legend(fontsize=spec.legend_fontsize, loc=spec.legend_loc, **LEGEND_KWARGS)
    _save_figure(fig, path)


def save_bar_chart(spec: BarChartSpec, path: Path) -> None:
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=spec.figsize, facecolor=BG_COLOR)
    apply_dark_style(ax)

    colors = list(spec.colors) if spec.colors else ["#3498db"] * len(spec.categories)
    bars = ax.bar(spec.categories, spec.values, color=colors, alpha=spec.bar_alpha)

    if spec.value_labels:
        for bar, label in zip(bars, spec.value_labels):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + spec.value_label_offset,
                label,
                ha="center",
                va="bottom",
                fontsize=spec.value_label_fontsize,
                color=spec.value_label_color,
            )

    _apply_axis_spec(ax, spec.axis)
    _save_figure(fig, path)
