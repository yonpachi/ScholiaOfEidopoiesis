# data/

SQLite マスターデータの管理ディレクトリ。

## 構成

| ディレクトリ | 内容 |
|-------------|------|
| `schema/` | テーブル定義 SQL（正） |
| `migrations/` | スキーマ変更履歴 SQL |
| `seeds/` | マスターデータ（CSV 等） |

## 正（Source of Truth）

SQL / CSV ファイルが正。`data/*.db` はそこから生成する成果物（`.gitignore` 対象）。

## 命名規則

- テーブル名・カラム名: 英語 snake_case
- スキーマ SQL: `{3桁番号}_{説明}.sql`（例: `001_init.sql`）

## DB の生成

`data/game.db` は SQL ファイルから再生成する（直接編集しない）。

**Commands → データベース → DBを再生成**

（`.vscode/tasks.json` のタスク `DBを再生成` を実行）

| 適用順 | 対象 |
|--------|------|
| 1 | `data/schema/*.sql`（番号順） |
| 2 | `data/seeds/*.sql`（番号順） |

- 実行のたびに `game.db` を作り直す（フルリビルド）
- `seeds/*.csv` の取り込みはテーブル定義後に拡張予定
- 生成後は SQLite Viewer で内容を確認できる
