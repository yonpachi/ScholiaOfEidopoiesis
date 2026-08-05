# 話し合いログ索引

議題ごとに `temp/` 以下へ個別ファイルを作成する。  
このファイルは索引のみ。詳細は各議論ファイルを参照。

## 実装方針（全作業共通）

```
話し合う → 議論ファイルにまとめる → Cursor Plan を作成 → 計画を実行
```

| 成果物           | 場所                                     |
| ---------------- | ---------------------------------------- |
| 議論ログ         | `temp/{番号}_{テーマ}.md`（議題ごと）    |
| 索引             | `temp/discussion_log.md`（このファイル） |
| 下書き           | `draft/rules/` 等（git 管理）            |
| 公開ドキュメント | `docs/`（GitHub Pages）                  |
| 計画書           | `.cursor/plans/*.plan.md`（Plan モード） |

## 命名規則

- 形式: `{3桁番号}_{テーマ}.md`（例: `001_project_foundation.md`）
- 1 議題・1 テーマ = 1 ファイル
- 長く続く議論はファイルを分け、索引に追記する

## ステータス凡例

- `[未決]` / `[議論中]` / `[決定]`

---

## 議論ファイル一覧

| #   | ファイル                                                   | テーマ                                                       | ステータス                     |
| --- | ---------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------ |
| 001 | [001_project_foundation.md](001_project_foundation.md)     | プロジェクト基盤（フロー・技術スタック・構成・命名・DB方針） | [決定]                         |
| 002 | [002_dice_system.md](002_dice_system.md)                   | ダイスシステム（適用場面・計算型・判定粒度・sim 目的）       | [決定] → `docs/rules/dice.md` |
| 003 | [003_game_design_overview.md](003_game_design_overview.md) | ゲーム設計概要（プレイ形式決定 2026-07-03 / キーワード開示保留） | [議論中]                       |
| 004 | [004_formatters.md](004_formatters.md)                     | フォーマッタ・リント導入（goimports / Ruff / golangci-lint） | [決定]                         |
| 005 | [005_races.md](005_races.md)                               | 種族・種族能力（判定時 **ほぼ確定** / 戦闘時 **先送り**・docs仮案） | [決定]（戦闘除く）             |
| 006 | [006_part3_race_avg.md](006_part3_race_avg.md)             | Part3 種族別平均スコア sim（8本線グラフ）                    | [決定]                         |
| 007 | [007_docs_dice_ancestry_revision.md](007_docs_dice_ancestry_revision.md) | ダイス・種族ルール文書の比較と改稿（backup vs docs）       | [決定]                         |
| 008 | [008_alchemy.md](008_alchemy.md)                                         | 錬金（**α″決定** / 数値・装備想成・タグは議論中）            | [議論中]                       |
| 009 | [009_world_setting.md](009_world_setting.md)                             | 世界観・背景（設計者向け下敷き）                             | [決定]（下敷き） / 地景ルール未 |
| 010 | [010_landscape.md](010_landscape.md)                                     | 地景・界標（据置・拓荒・隣接・解放条件）                     | [未決]                         |
| 011 | [011_combat.md](011_combat.md)                                           | 戦闘（**骨格・効果スキーマ一部決定** / 印記・数値は議論中）  | [議論中]                       |
| 012 | [012_marks_tags.md](012_marks_tags.md)                                   | 印記・タグ・効果文（**大部分決定** / 一覧は後日）            | [議論中]                       |
| 013 | [013_expression.md](013_expression.md)                                   | 式・計算・括弧記法（**除算・{} 決定** / 変数一覧は未）       | [議論中]                       |
| 014 | [014_lineage_proposals.md](014_lineage_proposals.md)                     | 系統案まとめ（txt/ 各AI回答の整理・比較）                    | [議論中]                       |
| 015 | [015_lineage_candidates.md](015_lineage_candidates.md)                   | 系統候補リスト（flash-idea / D1・フレーバー優先）            | [議論中]                       |
| 015 | [015_lineage_candidates_v2.md](015_lineage_candidates_v2.md)             | 系統候補リストv2（機能軸・クセ優先、flash-idea×D1統合）      | [議論中]                       |
| 016 | [016_light_dark_mana_substitution.md](016_light_dark_mana_substitution.md) | 光・闇マナの代用支払い（対立ペア／四属性集約）             | [議論中]                       |
| 017 | [017_lineage.md](017_lineage.md)                                         | アイテム系統（**β専門6**・札→歯車・召喚制限つき・造園） | [議論中]                       |
| 018 | [018_effect_catalog.md](018_effect_catalog.md)                           | 効果パターン表・**書き方テンプレ**（間合い等は本文外）       | [議論中]                       |
