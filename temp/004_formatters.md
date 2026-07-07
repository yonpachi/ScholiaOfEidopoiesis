# 004 フォーマッタ・リント導入



ステータス: [決定]



## 採用ツール



| 言語 | フォーマッタ | リント | 対象 |

|------|-------------|--------|------|

| Go | goimports | golangci-lint v2 | `pkg/`, `sim/` |

| Python | Ruff format | Ruff check | `macros.py`, `docs/`, `scripts/` |



## スコープ



- 保存時の自動フォーマット・リント（VS Code / Cursor 設定）

- Commands パレットから手動実行できるタスク（`.vscode/tasks.json`）

- CI・pre-commit は対象外



## 初回セットアップ（タスク化しない）



Go ツールは `%USERPROFILE%\go\bin\` にインストールし、タスクはそのバイナリを直接呼ぶ（`go run` は使わない。毎回依存を解決・コンパイルするため）。



```powershell

go install golang.org/x/tools/cmd/goimports@latest

go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.6.0

```



`.golangci.yml` は `version: "2"` 形式のため、golangci-lint **v2 系**が必要。



保存時フォーマット（エディタ）も Go 拡張が `%USERPROFILE%\go\bin\goimports.exe` を参照する。PATH に通していなくてもタスクは動作する。



Python 側は既存の「Python仮想環境を作成して依存をインストール」で `ruff` が入る。



## 初回適用



設定導入後、Commands → コード品質 から以下を 1 回ずつ実行する。



1. 全コードフォーマット

2. 全コードリント（指摘があれば修正）



## 参照



- 計画書: `.cursor/plans/フォーマッタ導入_8a825ba2.plan.md`

- 設定: `pyproject.toml`, `.golangci.yml`, `.vscode/settings.json`

