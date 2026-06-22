-- Game catalog DDL. Source of truth for table structure; apply to game.sqlite on change.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tag_kinds (
    id   TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS marks (
    id     TEXT PRIMARY KEY,
    name   TEXT NOT NULL UNIQUE,
    effect TEXT NOT NULL DEFAULT '',
    decay  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tags (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    mana        TEXT NOT NULL DEFAULT '',
    kind_id     TEXT REFERENCES tag_kinds (id),
    note        TEXT NOT NULL DEFAULT '',
    effect      TEXT NOT NULL DEFAULT '',
    restriction TEXT NOT NULL DEFAULT '',
    flag_fire   INTEGER NOT NULL DEFAULT 0 CHECK (flag_fire IN (0, 1)),
    flag_earth  INTEGER NOT NULL DEFAULT 0 CHECK (flag_earth IN (0, 1)),
    flag_water  INTEGER NOT NULL DEFAULT 0 CHECK (flag_water IN (0, 1)),
    flag_wind   INTEGER NOT NULL DEFAULT 0 CHECK (flag_wind IN (0, 1)),
    flag_dark   INTEGER NOT NULL DEFAULT 0 CHECK (flag_dark IN (0, 1)),
    flag_light  INTEGER NOT NULL DEFAULT 0 CHECK (flag_light IN (0, 1))
);

CREATE TABLE IF NOT EXISTS items (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL UNIQUE,
    timing            TEXT NOT NULL DEFAULT '',
    kind              TEXT NOT NULL DEFAULT '',
    difficulty        INTEGER,
    effect            TEXT NOT NULL DEFAULT '',
    note              TEXT NOT NULL DEFAULT '',
    creation_mana     TEXT NOT NULL DEFAULT '',
    entity_strength   TEXT NOT NULL DEFAULT '',
    strength          TEXT NOT NULL DEFAULT '',
    formula_strength  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS item_tags (
    item_id TEXT NOT NULL REFERENCES items (id) ON DELETE CASCADE,
    tag_id  TEXT NOT NULL REFERENCES tags (id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, tag_id)
);

CREATE TABLE IF NOT EXISTS weapons (
    id        TEXT PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    recipe    TEXT NOT NULL DEFAULT '',
    cost      TEXT NOT NULL DEFAULT '',
    flavor    TEXT NOT NULL DEFAULT '',
    effect    TEXT NOT NULL DEFAULT '',
    attribute TEXT NOT NULL DEFAULT '',
    grade     INTEGER,
    weight    TEXT NOT NULL DEFAULT '',
    flag_fire   INTEGER NOT NULL DEFAULT 0 CHECK (flag_fire IN (0, 1)),
    flag_earth  INTEGER NOT NULL DEFAULT 0 CHECK (flag_earth IN (0, 1)),
    flag_water  INTEGER NOT NULL DEFAULT 0 CHECK (flag_water IN (0, 1)),
    flag_wind   INTEGER NOT NULL DEFAULT 0 CHECK (flag_wind IN (0, 1)),
    flag_dark   INTEGER NOT NULL DEFAULT 0 CHECK (flag_dark IN (0, 1)),
    flag_light  INTEGER NOT NULL DEFAULT 0 CHECK (flag_light IN (0, 1))
);

CREATE TABLE IF NOT EXISTS armor (
    id        TEXT PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    recipe    TEXT NOT NULL DEFAULT '',
    cost      TEXT NOT NULL DEFAULT '',
    effect    TEXT NOT NULL DEFAULT '',
    grade     INTEGER,
    weight    TEXT NOT NULL DEFAULT '',
    flag_fire   INTEGER NOT NULL DEFAULT 0 CHECK (flag_fire IN (0, 1)),
    flag_earth  INTEGER NOT NULL DEFAULT 0 CHECK (flag_earth IN (0, 1)),
    flag_water  INTEGER NOT NULL DEFAULT 0 CHECK (flag_water IN (0, 1)),
    flag_wind   INTEGER NOT NULL DEFAULT 0 CHECK (flag_wind IN (0, 1)),
    flag_dark   INTEGER NOT NULL DEFAULT 0 CHECK (flag_dark IN (0, 1)),
    flag_light  INTEGER NOT NULL DEFAULT 0 CHECK (flag_light IN (0, 1))
);

CREATE TABLE IF NOT EXISTS terms (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    body       TEXT NOT NULL DEFAULT '',
    categories TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS scorions (
    id                    TEXT PRIMARY KEY,
    name                  TEXT NOT NULL UNIQUE,
    mana_bias             TEXT NOT NULL DEFAULT '',
    recommended_difficulty TEXT NOT NULL DEFAULT '',
    enemy_tendency        TEXT NOT NULL DEFAULT '',
    material_tendency     TEXT NOT NULL DEFAULT '',
    adjacency_effect      TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_tags_kind_id ON tags (kind_id);
CREATE INDEX IF NOT EXISTS idx_item_tags_tag_id ON item_tags (tag_id);
