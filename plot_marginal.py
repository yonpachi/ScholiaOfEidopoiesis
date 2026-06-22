"""
plot_marginal.py  ―  全フロー管理スクリプト

実行手順:
    python plot_marginal.py

処理の流れ:
    1. marginal/<YYYYMMDD_HHMMSS>/ フォルダを作成
    2. 現在のルールサマリー (rules.txt) をフォルダ内に生成
    3. monte_carlo.exe をそのフォルダを引数に呼び出し
       → Part1/Part2/Part3/Part4 のコンソール出力を result.txt に保存
       → marginal_by_n.csv, difficulty_table.csv,
          race_ability_by_n.csv, homunculus_option_distribution.csv
          をそのフォルダ内に生成
    4. 各CSV からグラフを生成してフォルダ内に保存
       → marginal_by_n.png           (Part2: 全ダイス限界貢献度)
       → difficulty_table.png        (Part3: 難易度テーブル)
       → race_ability_by_n.png       (Part4: 種族効果強さ比較)
       → homunculus_options.png      (Part4: ホムンクルス三択選択率)
"""

import csv
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # GUIなし環境でも動作
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ================================================================
# 設定
# ================================================================
SCRIPT_DIR   = Path(__file__).parent          # このスクリプトのあるフォルダ
EXE_PATH     = SCRIPT_DIR / "monte_carlo.exe"
MARGINAL_DIR = SCRIPT_DIR / "marginal"        # 出力ルートフォルダ

# 現在のルール設定（monte_carlo.c の設定と合わせて手動更新）
RULES = """\
=== 六種族ダイス TRPGルール (自動記録) ===
記録日時: {datetime}

【ダイスプール上限】
  最大 15個

【出目の読み方】
  d4 / d6 / d8 / d10 / d12 : 出目そのまま（出目1 = -1）
  d20                       : floor(出目 / 2)（出目1 = -1）

【最大値効果 共通ルール】
  - 全ダイスを一括でロールする
  - 最大値効果は任意の順で使用できる
  - 一度最大値効果を発動したダイスは以降の操作の対象にとれない（反応済み）
  - 自身は操作の対象にとれない
  - ダイス操作によって最大値になった場合、以降最大値効果を発動できる（連鎖）
  - 処理は1手順ずつ行われる

【各属性の最大値効果】
  火 (d4)  : 出目 >= 3  → 自身を4（最大値）に固定 + d4を1個追加ロール（連鎖可）
  地 (d6)  : 出目 == 6  → 未反応の1個を ±1/±2 循環調整（利得優先）
  風 (d8)  : 出目 == 8  → 未反応の偶数面ダイス1個を半回転（+N/2 循環、利得優先）
  闇 (d10) : 出目 == 10 → 未反応の1個を反転（N+1-出目、利得優先、連鎖可）
  光 (d12) : 出目 == 12 → 未反応の1個を最大値にセット（利得優先、連鎖可）
  水 (d20) : 出目 == 20 → プール内の出目1を1個→2に変換（-1ペナルティ解除）

【風モード】
  現在: WIND_HALFTURN（半回転モード: +N/2 循環）

【種族特殊能力】

  人間
    - 未反応ダイス1つの出目を反転（N+1-出目）
    - 使用コスト: -3（利得が3以下の場合は使用しない）

  獣人
    - 全ダイスの中から期待値が最も上がる1つを選んで振り直し
    - 新しい素目が元の素目より小さければ出目1（=-1ペナルティ）扱い
    - 振り直し後に反応済みフラグは立てない

  ホムンクルス（後出し三択、最良を自動選択）
    択A: 全ての-1ダイス（反応済み含む）を +1/個 かつ固定+1ボーナス
         ※ -1ダイスが1個以上必要
    択B: 未反応かつ非(-1)のダイス1つの出目を+1（上限=面数）かつ固定-2ペナルティ
    択C: 未反応ダイス1つの出目を循環-2（出目2→最大値、出目1→最大値-1）かつ固定-6ペナルティ

  付喪A（ツクモガミA）
    - 未反応ダイス1つの出目を循環+1
    - +1 後に反応条件を満たせば連鎖発動

  付喪B（ツクモガミB）
    - 未反応ダイス1つを「触媒」として、その面数の反応効果を他の未反応ダイスに適用
    - 効果上限: +5
    - 使用コスト: -1

  機械人
    - d10を1つd12に置換してロール（コスト -1）
"""

# ================================================================
# カラー・マーカー設定
# ================================================================
COLORS = {
    "d4":  "#e74c3c",   # 赤 (火)
    "d6":  "#8b4513",   # 茶 (地)
    "d8":  "#2ecc71",   # 緑 (風)
    "d10": "#9b59b6",   # 紫 (闇)
    "d20": "#3498db",   # 青 (水)
    "d12": "#f39c12",   # 金 (光)
}
MARKERS = {
    "d4": "o", "d6": "s", "d8": "^",
    "d10": "D", "d20": "v", "d12": "*"
}

# ================================================================
# Step 1: 出力フォルダ作成
# ================================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_dir = MARGINAL_DIR / timestamp
out_dir.mkdir(parents=True, exist_ok=True)
print(f"[1] 出力フォルダ作成: {out_dir}")

# ================================================================
# Step 2: rules.txt 生成
# ================================================================
rules_path = out_dir / "rules.txt"
rules_path.write_text(
    RULES.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    encoding="utf-8"
)
print(f"[2] ルールファイル生成: {rules_path.name}")

# ================================================================
# Step 3: monte_carlo.exe 実行（リアルタイムログ表示）
# ================================================================
if not EXE_PATH.exists():
    print(f"エラー: {EXE_PATH} が見つかりません。先にビルドしてください。")
    sys.exit(1)

result_path = out_dir / "result.txt"
print(f"[3] monte_carlo.exe 実行中...")

collected_lines = []  # result.txt 用に全行を蓄積

proc = subprocess.Popen(
    [str(EXE_PATH), str(out_dir)],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,   # stderr も stdout に混ぜる
    text=True,
    encoding="utf-8",
    errors="replace",
    cwd=str(SCRIPT_DIR),
    bufsize=1,                  # 行バッファ
)

assert proc.stdout is not None
prev_was_progress = False  # 直前が進捗行かどうか
for raw_line in proc.stdout:
    line = raw_line.rstrip("\n").rstrip("\r")
    collected_lines.append(line)

    if line.startswith("PROGRESS1:") or line.startswith("PROGRESS2:") or line.startswith("PROGRESS4:"):
        # 進捗行: \r で同じ行を上書き（改行なし）
        if line.startswith("PROGRESS1:"):
            tag = "[パス1]"
        elif line.startswith("PROGRESS2:"):
            tag = "[パス2]"
        else:
            tag = "[Part4]"
        body  = line.split(":", 1)[1].strip()
        print(f"\r    {tag} {body}    ", end="", flush=True)
        prev_was_progress = True
    else:
        if prev_was_progress:
            print()  # 進捗行の後は改行して次の行へ
            prev_was_progress = False
        print(f"    {line}", flush=True)

if prev_was_progress:
    print()

proc.wait()
if proc.returncode != 0:
    print(f"警告: monte_carlo.exe が終了コード {proc.returncode} で終了しました。")

# ================================================================
# Step 4: CSV 読み込み
# ================================================================
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

# ================================================================
# Step 5: グラフ生成（ダークモード）
# ================================================================
print("[5] グラフ生成中...")

plt.style.use("dark_background")

# ダークモード用にグリッド・スパイン色を調整するヘルパー
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

# ---- グラフ1: 全ダイス重ね合わせ ----
fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
ax.set_facecolor("#1a1a2e")
for name in dice_names:
    ax.plot(
        data[name]["x"], data[name]["y"],
        label=name,
        color=COLORS.get(name),
        marker=MARKERS.get(name, "o"),
        markersize=5, linewidth=2
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

print(f"\n完了。出力フォルダ: {out_dir}")

# ================================================================
# Step 6: 難易度テーブルグラフ生成
# ================================================================
diff_csv = out_dir / "difficulty_table.csv"
if not diff_csv.exists():
    print(f"警告: {diff_csv} が見つかりません。難易度グラフをスキップします。")
else:
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

    # 難易度ラベルと目標値ゾーン（ユーザー希望の成功率に合わせて後で調整）
    DIFF_LEVELS = [
        ("Easy(85%)",         85, "#44ff44"),
        ("Normal(70%)",       70, "#ffff44"),
        ("Hard(55%)",         55, "#ffaa22"),
        ("Very Hard(30%)",    30, "#ff4444"),
        ("Near Impossible(3%)", 3, "#ff00ff"),
    ]

    # カラー設定（プール名から属性色へ）
    COMBO_COLORS = {
        "d10only":       "#9b59b6",
        "d10+d4(Fire)":  "#e74c3c",
        "d10+d6(Earth)": "#8b4513",
        "d10+d8(Wind)":  "#2ecc71",
        "d10+d20(Water)":"#3498db",
    }
    COMBO_MARKERS = {
        "d10only":       "D",
        "d10+d4(Fire)":  "o",
        "d10+d6(Earth)": "s",
        "d10+d8(Wind)":  "^",
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
            markersize=4, linewidth=2
        )

    # 難易度水平線
    for label, pct, col in DIFF_LEVELS:
        ax.axhline(y=pct, color=col, linestyle="--", linewidth=1.0, alpha=0.6)
        ax.text(25.2, pct, label, color=col, fontsize=8.5,
                va="center", ha="left")

    ax.set_xlabel("Target value", fontsize=13)
    ax.set_ylabel("Success rate (%)", fontsize=13)
    ax.set_title("Difficulty Table: Success Rate by Target\n(1d10 + 1 Elemental Die)", fontsize=14)
    ax.set_xlim(1, 27)
    ax.set_ylim(-2, 103)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.legend(fontsize=11, loc="lower right",
              facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()

    out_diff = out_dir / "difficulty_table.png"
    fig.savefig(out_diff, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_diff.name}")

# ================================================================
# Step 7: 種族効果強さグラフ生成 (Part4)
#   y = use_rate × delta|use  (= avg_delta)
#   各点に use_rate と delta|use を小さく注記
# ================================================================
race_csv      = out_dir / "race_ability_by_n.csv"
use_rate_csv  = out_dir / "race_use_rate_by_n.csv"
delta_use_csv = out_dir / "race_delta_use_by_n.csv"

if not race_csv.exists():
    print(f"警告: {race_csv} が見つかりません。種族効果グラフをスキップします。")
else:
    print("[7] 種族効果強さグラフ生成中...")

    RACE_COLORS = {
        "Hume":        "#ffffff",   # 白
        "Makina":      "#f39c12",   # オレンジ
        "Bestia":      "#e74c3c",   # 赤
        "Homunculus":  "#2ecc71",   # 緑
        "Relicia":     "#d966ff",   # ピンク紫
        "Umbra":       "#ffff66",   # 黄
    }
    RACE_MARKERS = {
        "Hume":        "o",
        "Makina":      "D",
        "Bestia":      "^",
        "Homunculus":  "s",
        "Relicia":     "P",
        "Umbra":       "*",
    }

    def read_race_csv(path):
        """n_pool列とその他列を読み込み (names, {race: {x, y}}) を返す"""
        names, data = [], {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames is not None
            names = [c for c in reader.fieldnames if c != "n_pool"]
            for nm in names:
                data[nm] = {"x": [], "y": []}
            for row in reader:
                n = int(row["n_pool"])
                for nm in names:
                    v = row.get(nm, "").strip()
                    if v:
                        data[nm]["x"].append(n)
                        data[nm]["y"].append(float(v))
        return names, data

    race_names, avg_data = read_race_csv(race_csv)

    has_ur = use_rate_csv.exists()
    has_du = delta_use_csv.exists()
    ur_data = read_race_csv(use_rate_csv)[1] if has_ur else {}
    du_data = read_race_csv(delta_use_csv)[1] if has_du else {}

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG_COLOR)
    apply_dark_style(ax)

    for nm in race_names:
        xs = avg_data[nm]["x"]
        ys = avg_data[nm]["y"]   # = use_rate × delta|use (数学的に同値)
        color = RACE_COLORS.get(nm, "#ffffff")

        ax.plot(xs, ys,
                label=nm,
                color=color,
                marker=RACE_MARKERS.get(nm, "o"),
                markersize=5, linewidth=2)

        # 各点に「使用率 / 発動時効果量」をアノテーション
        if has_ur and has_du and nm in ur_data and nm in du_data:
            ur_map = dict(zip(ur_data[nm]["x"], ur_data[nm]["y"]))
            du_map = dict(zip(du_data[nm]["x"], du_data[nm]["y"]))
            for i, (x, y) in enumerate(zip(xs, ys)):
                ur = ur_map.get(x)
                du = du_map.get(x)
                if ur is None or du is None:
                    continue
                # 奇偶で上下交互に配置して隣接点の衝突を減らす
                va   = "bottom" if i % 2 == 0 else "top"
                yoff = 5        if i % 2 == 0 else -5
                ax.annotate(
                    f"u:{ur * 100:.0f}% d:{du:.1f}",
                    xy=(x, y),
                    xytext=(0, yoff),
                    textcoords="offset points",
                    fontsize=5,
                    color=color,
                    alpha=0.80,
                    va=va,
                    ha="center",
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
    ax.legend(fontsize=11, loc="upper left",
              facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()

    out_race = out_dir / "race_ability_by_n.png"
    fig.savefig(out_race, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_race.name}")

    # --- Step 7b: delta|use のみのグラフ ---
    if has_du:
        fig2, ax2 = plt.subplots(figsize=(14, 7), facecolor=BG_COLOR)
        apply_dark_style(ax2)

        for nm in race_names:
            if nm not in du_data:
                continue
            xs = du_data[nm]["x"]
            ys = du_data[nm]["y"]
            color = RACE_COLORS.get(nm, "#ffffff")
            ax2.plot(xs, ys,
                     label=nm,
                     color=color,
                     marker=RACE_MARKERS.get(nm, "o"),
                     markersize=5, linewidth=2)

        ax2.axhline(y=0, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5)
        ax2.set_xlabel("Total dice in pool (n_pool)", fontsize=13)
        ax2.set_ylabel("delta|use  (avg Δ when ability used)", fontsize=13)
        ax2.set_title(
            "Race Ability — delta|use per Pool Size\n"
            "  (effect magnitude when the ability fires, ignoring use rate)",
            fontsize=13,
        )
        ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax2.legend(fontsize=11, loc="upper left",
                   facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
        fig2.tight_layout()

        out_delta = out_dir / "race_delta_use_by_n.png"
        fig2.savefig(out_delta, dpi=150, facecolor=BG_COLOR)
        plt.close(fig2)
        print(f"    出力: {out_delta.name}")

# ================================================================
# Step 8: ホムンクルス三択選択率グラフ
# ================================================================
homo_csv = out_dir / "homunculus_option_distribution.csv"
if not homo_csv.exists():
    print(f"警告: {homo_csv} が見つかりません。ホムンクルスグラフをスキップします。")
else:
    print("[8] ホムンクルス三択グラフ生成中...")

    homo_labels = []
    homo_rates = []
    homo_counts = []

    with open(homo_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            homo_labels.append(row["option"])
            homo_counts.append(int(row["count"]))
            homo_rates.append(float(row["rate"]) * 100.0)

    fig, ax = plt.subplots(figsize=(7, 5), facecolor=BG_COLOR)
    apply_dark_style(ax)

    bar_colors = ["#2ecc71", "#e74c3c", "#3498db"]
    bars = ax.bar(homo_labels, homo_rates,
                  color=bar_colors[:len(homo_labels)], alpha=0.85)
    for bar, rate, count in zip(bars, homo_rates, homo_counts):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{rate:.1f}%\n(n={count:,})",
                ha="center", va="bottom", fontsize=10, color="#eeeeee")

    ax.set_ylabel("Selection rate (%)", fontsize=12)
    ax.set_title("Homunculus Option Selection Distribution", fontsize=13)
    ax.set_ylim(0, max(homo_rates) * 1.25 if homo_rates else 100)
    fig.tight_layout()

    out_homo = out_dir / "homunculus_options.png"
    fig.savefig(out_homo, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_homo.name}")

# ================================================================
# Step 9: ホムンクルス三択 n_pool別選択率グラフ
# ================================================================
homo_by_n_csv = out_dir / "homunculus_option_by_n.csv"
if not homo_by_n_csv.exists():
    print(f"警告: {homo_by_n_csv} が見つかりません。n別グラフをスキップします。")
else:
    print("[9] ホムンクルス三択 n別選択率グラフ生成中...")

    ns, a_rates, b_rates, c_rates = [], [], [], []
    with open(homo_by_n_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n = int(row["n_pool"])
            if n < 2:
                continue
            a = float(row["A_rate"]) * 100.0
            b = float(row["B_rate"]) * 100.0
            c = float(row["C_rate"]) * 100.0
            if a + b + c == 0.0:
                continue
            ns.append(n)
            a_rates.append(a)
            b_rates.append(b)
            c_rates.append(c)

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
    apply_dark_style(ax)

    opt_colors  = ["#2ecc71", "#e74c3c", "#3498db"]
    opt_labels  = ["A(エラー修正)", "B(改良・最大値固定)", "C(変異・全循環+1)"]
    opt_markers = ["o", "s", "^"]
    for rates, col, lbl, mrk in zip([a_rates, b_rates, c_rates],
                                     opt_colors, opt_labels, opt_markers):
        ax.plot(ns, rates, color=col, label=lbl, marker=mrk,
                linewidth=2, markersize=7)

    ax.set_xlabel("Total dice in pool (n_pool)", fontsize=12)
    ax.set_ylabel("Selection rate (%)", fontsize=12)
    ax.set_title("Homunculus Option Selection Rate per Pool Size", fontsize=13)
    ax.set_xticks(ns)
    ax.set_ylim(0, 65)
    ax.axhline(33.3, color="#555555", linewidth=0.8, linestyle="--")
    ax.legend(fontsize=10)
    fig.tight_layout()

    out_homo_n = out_dir / "homunculus_options_by_n.png"
    fig.savefig(out_homo_n, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_homo_n.name}")

# ================================================================
# Step 10: 1d10 + N×d4 合計達成値グラフ (Part5)
# ================================================================
d4_avg_csv = out_dir / "basic4_pool_avg.csv"
if not d4_avg_csv.exists():
    print(f"警告: {d4_avg_csv} が見つかりません。基本4ダイスプールグラフをスキップします。")
else:
    print("[10] 1d10 + N×ランダム基本4ダイス 合計達成値グラフ生成中...")

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

    ax.plot(ns_d4, avgs, color="#e74c3c", marker="o", markersize=6,
            linewidth=2, label="avg (平均)")
    ax.plot(ns_d4, p50s, color="#f39c12", marker="s", markersize=5,
            linewidth=1.5, linestyle="--", label="p50 (中央値)")
    ax.plot(ns_d4, p90s, color="#2ecc71", marker="^", markersize=5,
            linewidth=1.5, linestyle=":", label="p90 (90パーセンタイル)")
    ax.plot(ns_d4, p99s, color="#3498db", marker="D", markersize=5,
            linewidth=1.5, linestyle="-.", label="p99 (99パーセンタイル)")

    # 各avgの値をアノテーション
    for x, y in zip(ns_d4, avgs):
        ax.annotate(f"{y:.1f}",
                    xy=(x, y), xytext=(0, 8),
                    textcoords="offset points",
                    fontsize=9, color="#e74c3c",
                    ha="center", va="bottom")

    # テストプレイ序盤想定ライン（追加2〜3個）
    ax.axvspan(2, 3, alpha=0.08, color="#ffffff", label="序盤想定範囲 (2〜3個)")

    ax.set_xlabel("Number of extra dice (N)", fontsize=13)
    ax.set_ylabel("Total achievement value", fontsize=13)
    ax.set_title(
        "1d10 (fixed) + N × Random Basic-4 Dice {d4,d6,d8,d20}\n"
        "  Total Expected Achievement Value (with chain reaction simulation)",
        fontsize=14
    )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.legend(fontsize=11, loc="upper left",
              facecolor="#2a2a3e", edgecolor="#555555", labelcolor="#eeeeee")
    fig.tight_layout()

    out_d4 = out_dir / "basic4_pool_avg.png"
    fig.savefig(out_d4, dpi=150, facecolor=BG_COLOR)
    plt.close(fig)
    print(f"    出力: {out_d4.name}")

print(f"\n全処理完了。出力フォルダ: {out_dir}")
