# sim/

Go 製エミュレーター。ゲームバランスの検証（モンテカルロ法など）に使用する。

## 構成

```
sim/
├── part1/          # 限界貢献度シミュレーション（旧 backup part2）
├── part2/          # 種族判定時能力比較（旧 backup part4）
├── part3/          # 種族別平均スコア（8本線グラフ）
├── part4/          # 品質 × 再錬金回数（最良）と武器等級表
├── _common.py      # Python 共通ヘルパー
├── plotting.py     # グラフ描画共通
├── bin/            # ビルド成果物（gitignore）
└── main.go         # 将来の統合エントリ（現状スタブ）
```

- ダイスエンジン: `pkg/dice/`
- 種族能力: `pkg/ancestry/`
- 実行結果（CSV・PNG）: プロジェクトルートの `result/<タイムスタンプ>/`（sim 外）
- ビルド成果物: `sim/bin/`（`.gitignore` 対象）

## コマンド

**Commands → エミュレーター** から実行する。

| コマンド | 内容 |
|---------|------|
| Go mod tidy (sim) | 依存関係を整理 |
| Goテスト (sim) | `go test ./...` |
| Goビルド (sim) | `bin/sim.exe` / `part1.exe` / `part2.exe` / `part3.exe` / `part4.exe` を生成 |
| Part1限界貢献度 | 列挙シム → CSV → PNG |
| Part2種族能力 | 種族能力比較 sim → CSV → PNG |
| Part3種族平均スコア | 種族別平均スコア sim → CSV → PNG |
| Part4品質試行 | マナ別・再錬金 k 回の最良品質 → 雑魚25到達と武器等級表 |
| 全Part実行 | `sim/partN/run.py` を番号順に一括実行（`result/<timestamp>/` に集約） |

## Part1 の出力

`result/<タイムスタンプ>/` に以下が生成される。

| ファイル | 内容 |
|---------|------|
| `csv/marginal_by_n.csv` | 他ダイス数別・種別（d4〜d20, d12）の限界貢献度 |
| `marginal_by_n.png` | 折れ線グラフ |

## Part2 の出力

| ファイル | 内容 |
|---------|------|
| `csv/race_ability_by_n.csv` | n_pool × 種族 avg_delta（ベースd10 + レシピd4/d6/d8/d20） |
| `csv/race_use_rate_by_n.csv` | 能力使用率 |
| `csv/race_delta_use_by_n.csv` | 使用時 avg_delta |
| `csv/homunculus_option_distribution.csv` | 進化3択の選択率（全体） |
| `csv/homunculus_option_by_n.csv` | 進化3択の選択率（n_pool 別） |
| `race_ability_by_n.png` | 折れ線グラフ |
| `homunculus_options.png` | ホムンクルス三択棒グラフ（全体） |
| `homunculus_options_by_n.png` | ホムンクルス三択折れ線グラフ（マナ別） |

## Part3 の出力

| ファイル | 内容 |
|---------|------|
| `csv/race_score_by_n.csv` | n_pool × Baseline + 6種族 + RaceMean の平均達成値 |
| `csv/race_score_pct_by_n.csv` | 同上を 6種族平均比（%）に変換（0% = RaceMean） |
| `race_score_by_n.png` | 8本折れ線グラフ（種族なし / 6種族 / 試行内6種族平均） |
| `race_score_pct_by_n.png` | 7本折れ線グラフ（種族平均比、0% 基準） |

## Part4 の出力

種族なし。各マナ（n_pool−1）について、レシピ構成は均等重みで選び、同一構成を k 回錬金して最良品質を採用。初期並雑魚 HP 20。武器は中量×中行動（⌊品質÷等級⌋×6）。

| ファイル | 内容 |
|---------|------|
| `csv/quality_by_mana_k.csv` | マナ × k の avg / p50 / p99 / 雑魚到達率 |
| `csv/quality_avg_by_k.csv` | 横軸 k、列＝マナ（平均） |
| `csv/quality_p50_by_k.csv` | 同上（中央値） |
| `csv/quality_p99_by_k.csv` | 同上（p99） |
| `csv/quality_reach_by_k.csv` | P(最良 ≥ 25) |
| `csv/trash_reach_k.csv` | 各マナで avg/p50/p99/到達率50% が 25 に届く最小 k |
| `csv/weapon_grade.csv` | 等級ごとの中量中1撃・雑魚手数・PC 5撃 HP |
| `quality_p50_by_k.png` / `quality_avg_by_k.png` / `quality_p99_by_k.png` | 再錬金回数と最良品質 |
| `quality_reach_by_k.png` | 並雑魚一撃率 |
| `weapon_grade_hit.png` | 等級 → 1撃（2マナ未鍛錬 p50） |

## モジュール

```
github.com/yonpachi/ScholiaOfEidopoiesis
```
