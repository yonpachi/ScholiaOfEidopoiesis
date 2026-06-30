# sim/

Go 製エミュレーター。ゲームバランスの検証（モンテカルロ法など）に使用する。

## 構成

```
sim/
├── part1/          # 限界貢献度シミュレーション（旧 backup part2）
├── part2/          # 種族判定時能力比較（旧 backup part4）
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
| Goビルド (sim) | `bin/sim.exe` / `part1.exe` / `part2.exe` を生成 |
| Part1限界貢献度 | 列挙シム → CSV → PNG |
| Part2種族能力 | 種族能力比較 sim → CSV → PNG |

## Part1 の出力

`result/<タイムスタンプ>/` に以下が生成される。

| ファイル | 内容 |
|---------|------|
| `csv/marginal_by_n.csv` | 他ダイス数別・種別の限界貢献度 |
| `marginal_by_n.png` | 折れ線グラフ |

## Part2 の出力

| ファイル | 内容 |
|---------|------|
| `csv/race_ability_by_n.csv` | n_pool × 種族 avg_delta |
| `csv/race_use_rate_by_n.csv` | 能力使用率 |
| `csv/race_delta_use_by_n.csv` | 使用時 avg_delta |
| `csv/homunculus_option_distribution.csv` | 進化3択の選択率 |
| `race_ability_by_n.png` | 折れ線グラフ |
| `homunculus_options.png` | ホムンクルス棒グラフ |

## モジュール

```
github.com/yonpachi/ScholiaOfEidopoiesis
```
