"""
plot_marginal.py  ―  全フロー管理スクリプト

実行手順:
    python plot/plot_marginal.py

処理の流れ:
    1. data/<YYYYMMDD_HHMMSS>/ フォルダを作成
    2. 現在のルールサマリー (rules.txt) をフォルダ内に生成
    3. monte_carlo.exe をそのフォルダを引数に呼び出し
    4. 各CSV からグラフを生成してフォルダ内に保存
"""

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ================================================================
# 設定
# ================================================================
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
EXE_PATH = ROOT_DIR / "monte_carlo.exe"
DATA_DIR = ROOT_DIR / "data"

RULES = """\
=== 六種族ダイス TRPGルール (自動記録) ===
記録日時: {datetime}

【ダイスプール上限】
  最大 10個 (MAX_N)

【出目の読み方】
  d4 / d6 / d8 / d10 / d12 : 出目そのまま（出目1 = -1）
  d20                       : floor(出目 / 2)（出目1-3 = -1）

【反応効果 共通ルール】
  - 全ダイスを一括でロールする
  - 反応は任意の順で使用できる（利得>0のときのみ）
  - 一度反応したダイスは以降の操作の対象にとれない（反応済み）
  - 自身は操作の対象にとれない
  - ダイス操作によってトリガー条件を満たした場合、連鎖可
  - 処理は1手順ずつ行われる

【各属性の反応効果】
  火 (d4)  : 出目 >= 3  → 自身を4 + d4を1個追加（連鎖可）
  地 (d6)  : 出目 == 6  → 未反応の1個を ±1/±2 循環調整（利得優先）
  風 (d8)  : 出目 == 8  → 未反応の偶数面ダイス1個を半回転（利得優先）
  闇 (d10) : 出目 == 10 → 未反応の1個を反転（利得優先、連鎖可）
  光 (d12) : 出目 == 12 → 未反応の1個を最大値に（利得優先、連鎖可）
  水 (d20) : 出目 == 20 → 未反応の1個を振り直し（期待利得優先、連鎖可）

【風モード】
  現在: WIND_HALFTURN（半回転モード: +N/2 循環）
"""

COLORS = {
    "d4": "#e74c3c",
    "d6": "#8b4513",
    "d8": "#2ecc71",
    "d10": "#9b59b6",
    "d20": "#3498db",
    "d12": "#f39c12",
}
MARKERS = {
    "d4": "o", "d6": "s", "d8": "^",
    "d10": "D", "d20": "v", "d12": "*",
}

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = DATA_DIR / timestamp
out_dir.mkdir(parents=True, exist_ok=True)
print(f"[1] 出力フォルダ作成: {out_dir}")

rules_path = out_dir / "rules.txt"
rules_path.write_text(
    RULES.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    encoding="utf-8",
)
print(f"[2] ルールファイル生成: {rules_path.name}")

if not EXE_PATH.exists():
    print(f"エラー: {EXE_PATH} が見つかりません。先にビルドしてください。")
    sys.exit(1)

print(f"[3] monte_carlo.exe 実行中...")
collected_lines = []
proc = subprocess.Popen(
    [str(EXE_PATH), str(out_dir)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
    cwd=str(ROOT_DIR),
    bufsize=1,
)

assert proc.stdout is not None
prev_was_progress = False
for raw_line in proc.stdout:
    line = raw_line.rstrip("\n").rstrip("\r")
    collected_lines.append(line)

    if line.startswith(("PROGRESS1:", "PROGRESS2:", "PROGRESS4:")):
        if line.startswith("PROGRESS1:"):
            tag = "[パス1]"
        elif line.startswith("PROGRESS2:"):
            tag = "[パス2]"
        else:
            tag = "[Part4]"
        body = line.split(":", 1)[1].strip()
        print(f"\r    {tag} {body}    ", end="", flush=True)
        prev_was_progress = True
    else:
        if prev_was_progress:
            print()
            prev_was_progress = False
        print(f"    {line}", flush=True)

if prev_was_progress:
    print()

proc.wait()
if proc.returncode != 0:
    print(f"警告: monte_carlo.exe が終了コード {proc.returncode} で終了しました。")

csv_path = out_dir / "marginal_by_n.csv"
if not csv_path.exists():
    print(f"エラー: {csv_path} が生成されていません。")
    sys.exit(1)

dice_names = []
data = {}

with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    assert reader.fieldnames is not None
    dice_names = [col for col in reader.fieldnames if col != "n_others"]
    for name in dice_names:
        data[name] = {"x": [], "y": []}
    for row in reader:
        n = int(row["n_others"])
        for name in dice_names:
            val = row[name]
            if val.strip() != "":
                data[name]["x"].append(n)
                data[name]["y"].append(float(val))

print(f"[4] CSV読み込み完了: {dice_names}")
print("[5] グラフ生成中...")

plt.style.use("dark_background")


def apply_dark_style(ax):
    ax.set_facecolor("#1a1a2e")
    ax.grid(True, linestyle="--", alpha=0.3, color="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#555555")
    ax.tick_params(colors="#cccccc")
    ax.xaxis.label.set_color("#cccccc")
    ax.yaxis.label.set_color("#cccccc")
    ax.title.set_color("#eeeeee")


BG_COLOR = "#0f0f1a"

fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
ax.set_facecolor("#1a1a2e")
for name in dice_names:
    ax.plot(
        data[name]["x"], data[name]["y"],
        label=name,
        color=COLORS.get(name),
        marker=MARKERS.get(name, "o"),
        markersize=5, linewidth=2,
    )
ax.set_xlabel("Number of other dice (n_others)", fontsize=13)
ax.set_ylabel("Marginal contribution (avg)", fontsize=13)
ax.set_title("Marginal Contribution by Dice Type vs Other Dice Count", fontsize=15)
ax.legend(fontsize=12, loc="lower right", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
apply_dark_style(ax)
fig.tight_layout()
out1 = out_dir / "marginal_by_n.png"
fig.savefig(out1, dpi=150, facecolor=BG_COLOR)
plt.close(fig)
print(f"    出力: {out1.name}")

diff_csv = out_dir / "difficulty_table.csv"
if diff_csv.exists():
    print("[6] 難易度テーブルグラフ生成中...")
    diff_dice_names = []
    diff_data = {}
    with open(diff_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        diff_dice_names = [col for col in reader.fieldnames if col != "target"]
        for name in diff_dice_names:
            diff_data[name] = {"x": [], "y": []}
        for row in reader:
            tgt = int(row["target"])
            for name in diff_dice_names:
                val = row[name]
                if val.strip() != "":
                    diff_data[name]["x"].append(tgt)
                    diff_data[name]["y"].append(float(val) * 100.0)

    DIFF_LEVELS = [
        ("Easy(85%)", 85, "#44ff44"),
        ("Normal(70%)", 70, "#ffff44"),
        ("Hard(55%)", 55, "#ffaa22"),
        ("Very Hard(30%)", 30, "#ff4444"),
        ("Near Impossible(3%)", 3, "#ff00ff"),
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

    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG_COLOR)
    apply_dark_style(ax)
    for name in diff_dice_names:
        ax.plot(
            diff_data[name]["x"], diff_data[name]["y"],
            label=name,
            color=COMBO_COLORS.get(name, "#ffffff"),
            marker=COMBO_MARKERS.get(name, "o"),
            markersize=4, linewidth=2,
        )
    for label, pct, col in DIFF_LEVELS:
        ax.axhline(y=pct, color=col, linestyle="--", linewidth=1.0, alpha=0.6)
        ax.text(25.2, pct, label, color=col, fontsize=8.5, va="center", ha="left")
    ax.set_xlabel("Target value", fontsize=13)
    ax.set_ylabel("Success rate (%)", fontsize=13)
    ax.set_title("Difficulty Table: Success Rate by Target\n(1d10 + 1 Elemental Die)", fontsize=14)
    ax.set_xlim(1, 27)
    ax.set_ylim(-2, 103)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.legend(fontsize=11, loc="lower right", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_diff = out_dir / "difficulty_table.png"
    fig.savefig(out_diff, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_diff.name}")

race_csv = out_dir / "race_ability_by_n.csv"
use_rate_csv = out_dir / "race_use_rate_by_n.csv"
delta_use_csv = out_dir / "race_delta_use_by_n.csv"

if race_csv.exists():
    print("[7] 種族効果強さグラフ生成中...")

    RACE_COLORS = {
        "Hume": "#ffffff", "Makina": "#f39c12", "Bestia": "#e74c3c",
        "Homunculus": "#2ecc71", "Relicia": "#d966ff", "Umbra": "#ffff66",
    }
    RACE_MARKERS = {
        "Hume": "o", "Makina": "D", "Bestia": "^",
        "Homunculus": "s", "Relicia": "P", "Umbra": "*",
    }

    def read_race_csv(path):
        names, data_out = [], {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames is not None
            names = [c for c in reader.fieldnames if c != "n_pool"]
            for nm in names:
                data_out[nm] = {"x": [], "y": []}
            for row in reader:
                n = int(row["n_pool"])
                for nm in names:
                    v = row.get(nm, "").strip()
                    if v:
                        data_out[nm]["x"].append(n)
                        data_out[nm]["y"].append(float(v))
        return names, data_out

    race_names, avg_data = read_race_csv(race_csv)
    has_ur = use_rate_csv.exists()
    has_du = delta_use_csv.exists()
    ur_data = read_race_csv(use_rate_csv)[1] if has_ur else {}
    du_data = read_race_csv(delta_use_csv)[1] if has_du else {}

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG_COLOR)
    apply_dark_style(ax)
    for nm in race_names:
        xs = avg_data[nm]["x"]
        ys = avg_data[nm]["y"]
        color = RACE_COLORS.get(nm, "#ffffff")
        ax.plot(xs, ys, label=nm, color=color, marker=RACE_MARKERS.get(nm, "o"), markersize=5, linewidth=2)
        if has_ur and has_du and nm in ur_data and nm in du_data:
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
                    f"u:{ur * 100:.0f}% d:{du:.1f}",
                    xy=(x, y), xytext=(0, yoff), textcoords="offset points",
                    fontsize=5, color=color, alpha=0.80, va=va, ha="center",
                )
    ax.axhline(y=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Total dice in pool (n_pool)", fontsize=13)
    ax.set_ylabel("use_rate × delta|use  (= avg Δ)", fontsize=13)
    ax.set_title(
        "Race Ability Strength — use_rate × delta|use per Pool Size\n"
        "  annotations: u = use rate,  d = avg Δ when used",
        fontsize=13,
    )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.legend(fontsize=11, loc="upper left", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_race = out_dir / "race_ability_by_n.png"
    fig.savefig(out_race, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_race.name}")

homo_csv = out_dir / "homunculus_option_distribution.csv"
if homo_csv.exists():
    print("[8] ホムンクルス三択グラフ生成中...")
    homo_labels, homo_rates, homo_counts = [], [], []
    with open(homo_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            homo_labels.append(row["option"])
            homo_counts.append(int(row["count"]))
            homo_rates.append(float(row["rate"]) * 100.0)
    fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG_COLOR)
    apply_dark_style(ax)
    bar_colors = ["#2ecc71", "#e74c3c", "#3498db"]
    bars = ax.bar(homo_labels, homo_rates, color=bar_colors[:len(homo_labels)], alpha=0.85)
    for bar, rate, count in zip(bars, homo_rates, homo_counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
            f"{rate:.1f}%\n(n={count:,})", ha="center", va="bottom", fontsize=10, color="#eeeeee",
        )
    ax.set_ylabel("Selection rate (%)", fontsize=12)
    ax.set_title("Homunculus Option Selection Distribution", fontsize=13)
    ax.set_ylim(0, max(homo_rates) * 1.25 if homo_rates else 100)
    fig.tight_layout()
    out_homo = out_dir / "homunculus_options.png"
    fig.savefig(out_homo, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_homo.name}")

d4_avg_csv = out_dir / "basic4_pool_avg.csv"
if d4_avg_csv.exists():
    print("[10] basic4 プールグラフ生成中...")
    ns_d4, avgs, p50s, p90s, p99s = [], [], [], [], []
    with open(d4_avg_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ns_d4.append(int(row["n_extra"]))
            avgs.append(float(row["avg"]))
            p50s.append(int(row["p50"]))
            p90s.append(int(row["p90"]))
            p99s.append(int(row["p99"]))
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG_COLOR)
    apply_dark_style(ax)
    ax.plot(ns_d4, avgs, color="#e74c3c", marker="o", markersize=6, linewidth=2, label="avg (平均)")
    ax.plot(ns_d4, p50s, color="#f39c12", marker="s", markersize=5, linewidth=1.5, linestyle="--", label="p50")
    ax.plot(ns_d4, p90s, color="#2ecc71", marker="^", markersize=5, linewidth=1.5, linestyle=":", label="p90")
    ax.plot(ns_d4, p99s, color="#3498db", marker="D", markersize=5, linewidth=1.5, linestyle="-.", label="p99")
    for x, y in zip(ns_d4, avgs):
        ax.annotate(f"{y:.1f}", xy=(x, y), xytext=(0, 8), textcoords="offset points", fontsize=9, color="#e74c3c", ha="center", va="bottom")
    ax.axvspan(2, 3, alpha=0.08, color="#ffffff", label="序盤想定範囲 (2〜3個)")
    ax.set_xlabel("Number of extra dice (N)", fontsize=13)
    ax.set_ylabel("Total achievement value", fontsize=13)
    ax.set_title("1d10 + N × Random Basic-4 Dice", fontsize=14)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.legend(fontsize=11, loc="upper left", facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()
    out_d4 = out_dir / "basic4_pool_avg.png"
    fig.savefig(out_d4, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_d4.name}")

print(f"\n全処理完了。出力フォルダ: {out_dir}")
