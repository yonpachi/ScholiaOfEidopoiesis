# 001: プロジェクト基盤の設計

**日付:** 2026-06-30  
**ステータス:** [決定]

---

## 議題 1: Cursor との作業フロー・ルール構成

**決定事項:**
- AI の役割: 両者が平等に議論しながら共同設計する（co-design）
- 編集スタイル: 必ず Plan モードで計画を提示し、承認を得てから作業する（慎重派）
- git コミット: ユーザーが任意のタイミングで行う（AI はコミットしない）
- AI が迷ったとき: 必ず質問してから進む
- temp/ の git 管理: .gitignore に追加して管理外にする

---

## 議題 2: 技術スタック

**決定事項:**
- GitHub Pages ドキュメントツール: MkDocs + Material テーマ（Python）
- DB: SQLite + 生 SQL（ORM なし、SQLite Viewer 拡張で UI 操作）
- エミュレーター言語: Go（速度と書きやすさのバランス、モンテカルロ法に最適）

---

## 議題 3: ディレクトリ構成

**決定事項:**

コロケーション原則に従い、ツール軸ベースの構成を基本とし、関連ファイルは同一機能名を共有する。

```
錬金術TRPG/
├── .cursor/rules/
├── docs/                       # MkDocs（GitHub Pages）
│   ├── rules/
│   ├── macros.py
│   └── glossary.md
├── data/
│   ├── schema/
│   ├── migrations/
│   └── seeds/
├── constants/
├── sim/
├── temp/
├── mkdocs.yml
└── requirements.txt
```

- constants/ は JSON 形式：Go と MkDocs 両方から参照
- 同一機能の関連ファイルは同じ名前を共有（例: `combat.json` / `combat.md` / `combat_seeds.csv`）

---

## 議題 4: 言語方針・命名規則

**決定事項:**
- クラス名: PascalCase（例: `ItemData`, `PlayerCharacter`）
- 変数名・関数名: camelCase（例: `itemName`, `calculateDamage`）
- ファイル名: snake_case（例: `item_data.py`, `game_rules.md`）
- ドキュメント・コメント: 日本語
- git コミット: ユーザーが自分で行う（AI は関与しない・形式指定なし）

---

## 議題 5: ゲームルール設計の進め方

**決定事項:**
- 優先順位: まず技術環境（GitHub Pages・DB セットアップ）を完成させる
- ゲームルールの設計フロー: チャットで話し合い → temp/ にメモ → draft/ に下書き → docs/ に正式化

---

## 議題 6: データの正（Source of Truth）

**決定事項:**
- 方針 1 を採用: **SQL / CSV ファイルが正**、`.db` はそこから生成・更新する
- `data/schema/`、`data/migrations/`、`data/seeds/` を git 管理する
- `.db` は生成物（直接編集しない。SQLite Viewer は確認・デバッグ用）
- AI も SQL / CSV を編集し、適用して DB を更新する
