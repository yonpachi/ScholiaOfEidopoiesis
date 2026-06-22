# ゲームカタログ（SQLite）

アイテム・タグ・印記・武器・防具・用語・スコーリオンなどの**ゲームデータ正本**。
ルール本文は [`docs/`](../docs/) を参照すること。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `game.sqlite` | 実データ（編集対象） |
| `schema.sql` | テーブル定義（DDL の git 正本） |
| `views.sql` | 一覧ページ相当の VIEW（Notion リンクド DB のミラー） |
| `queries/` | 管理用・検証用の保存 SQL |

## 三層の位置づけ

| 層 | 正本 | 用途 |
| --- | --- | --- |
| `docs/` | ルール（メカニクス） | GM・制作者・シム設計 |
| `catalog/` | ゲームデータ（本ディレクトリ） | 開発・シム参照 |
| Notion | PL 提示用ミラー | プレイヤー向け公開（手動更新） |

`html/` は Notion エクスポートのスナップショット。初回移行の入力源として使い、以降の開発編集面には使わない。

## Cursor での編集

1. **SQLite Viewer** 拡張を入れる（`.vscode/extensions.json` に推奨記載あり）
2. `catalog/game.sqlite` を開き、テーブルまたは VIEW を表形式で表示・編集
3. 一覧確認: `v_marks_list`, `v_tags_list`, `v_items_list` など（[`views.sql`](views.sql)）
4. 横断確認: [`queries/admin_overview.sql`](queries/admin_overview.sql) などを Viewer で実行

### DDL を変えたとき

1. [`schema.sql`](schema.sql) を更新
2. `python scripts/init_catalog_db.py` で空 DB を再生成するか、既存 DB に `ALTER TABLE`
3. [`views.sql`](views.sql) を必要に応じて更新し、Viewer または `init_catalog_db.py` で再適用
4. データを移し直す場合は `python scripts/migrate_notion_export.py`（`html/` から再投入）

## 整合チェック

リポジトリルートまたは `sim/` から:

```bash
go run ./sim/validate-catalog
# または
go test ./sim/catalog/...
```

チェック内容:

- 印記・タグ・アイテム等の名前重複なし
- タグ名と印記名の同名衝突なし
- `item_tags` の参照整合
- 武器・防具・アイテム効果文内の `<印記>` が `marks` に存在

## sim からの参照

```go
import "github.com/yonpachi/ScholiaOfEidopoiesis/sim/catalog"

cat, err := catalog.Open("") // catalog/game.sqlite を自動解決
defer cat.Close()

mark, err := cat.MarkByName("毒")
tags, err := cat.TagsForItemName("失敗作")
```

環境変数 `CATALOG_PATH` で DB パスを上書きできる。

## テーブル一覧

| テーブル | 内容 | id 形式 |
| --- | --- | --- |
| `marks` | 印記 | `mark_<名前>` |
| `tags` | タグ | `tag_<名前>` |
| `tag_kinds` | タグ種別マスタ | `kind_<名前>` |
| `items` | アイテム | `item_<名前>` |
| `item_tags` | アイテム↔タグ | 複合 PK |
| `weapons` | 武器 | `weapon_<名前>` |
| `armor` | 防具 | `armor_<名前>` |
| `terms` | 用語 | `term_<名前>` |
| `scorions` | スコーリオン | `scorion_<名前>` |

## 初回移行（html エクスポート）

```bash
python scripts/migrate_notion_export.py
```

Notion の HTML/CSV エクスポート（[`html/`](../html/)）から `game.sqlite` を生成する。

## 将来: Notion エクスポート（未実装）

API 連携は行わない。片方向の CSV エクスポートのみ想定:

```bash
# 将来のイメージ（未実装）
python scripts/export_notion_csv.py --view v_marks_list -o export/印記一覧.csv
```

設計方針:

- **VIEW ごとに 1 CSV** → Notion の「ページごとのリンクド DB」と 1:1 対応
- リレーション列は Notion インポート形式（ページ名 + 相対パス）に変換
- 生成した CSV を Notion に手動インポートして PL ミラーを更新

## Notion との運用

- **編集の正本**: 本ディレクトリ（開発時）
- **PL への反映**: Notion を手動更新（または将来エクスポート CSV をインポート）
- カタログを変更したセッションでは、PL 公開が必要なら Notion も同セッションで更新することを推奨
