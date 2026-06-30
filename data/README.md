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
