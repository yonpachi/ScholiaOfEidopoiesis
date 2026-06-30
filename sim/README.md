# sim/

Go 製エミュレーター。ゲームバランスの検証（モンテカルロ法など）に使用する。

## 構成

```
sim/
├── part1/          # 限界貢献度シミュレーション（旧 backup part2）
├── _common.py      # Python 共通ヘルパー
├── plotting.py     # グラフ描画共通
├── bin/            # ビルド成果物（gitignore）
└── main.go         # 将来の統合エントリ（現状スタブ）
```

- ダイスエンジン: `pkg/dice/`
- 実行結果（CSV・PNG）: プロジェクトルートの `result/<タイムスタンプ>/`（sim 外）
- ビルド成果物: `sim/bin/`（`.gitignore` 対象）

## コマンド

**Commands → エミュレーター** から実行する。

| コマンド | 内容 |
|---------|------|
| Go mod tidy (sim) | 依存関係を整理 |
| Goテスト (sim) | `go test ./...` |
| Goビルド (sim) | `bin/sim.exe` と `bin/part1.exe` を生成 |
| Part1限界貢献度(sim+グラフ) | 列挙シム実行 → CSV → PNG |
| Part1グラフのみ | 直近の `result/<タイムスタンプ>/` から PNG 再生成 |

## Part1 の出力

`result/<タイムスタンプ>/` に以下が生成される。

| ファイル | 内容 |
|---------|------|
| `csv/marginal_by_n.csv` | 他ダイス数別・種別の限界貢献度 |
| `marginal_by_n.png` | 折れ線グラフ |

## モジュール

```
github.com/yonpachi/ScholiaOfEidopoiesis
```
