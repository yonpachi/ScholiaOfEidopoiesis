# sim/

Go 製エミュレーター。ゲームバランスの検証（モンテカルロ法など）に使用する。

## 構成

- 定数: 実行時に `../constants/*.json` を読み込む（ハードコードしない）
- ビルド成果物: `bin/`（`.gitignore` 対象）

## コマンド

**Commands → エミュレーター** から実行する。

| コマンド | 内容 |
|---------|------|
| Go mod tidy (sim) | 依存関係を整理 |
| Goテスト (sim) | `go test ./...` |
| Goビルド (sim) | `bin/sim.exe` を生成 |

## モジュール

```
github.com/yonpachi/ScholiaOfEidopoiesis/sim
```
