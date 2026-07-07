-- 001_init.sql
-- 初期スキーマ: スキーマ管理用テーブルのみ
-- ゲームデータのテーブルはルール設計後に追加する

CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO schema_version (version, name)
VALUES (1, '001_init');
