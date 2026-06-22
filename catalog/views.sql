-- List-page mirrors (Notion linked-DB equivalents). Re-apply after schema changes.

DROP VIEW IF EXISTS v_marks_list;
CREATE VIEW v_marks_list AS
SELECT id, name, effect, decay
FROM marks
ORDER BY name;

DROP VIEW IF EXISTS v_tags_list;
CREATE VIEW v_tags_list AS
SELECT
    t.id,
    t.name,
    t.mana,
    k.name AS kind_name,
    t.note,
    t.effect,
    t.restriction,
    t.flag_fire,
    t.flag_earth,
    t.flag_water,
    t.flag_wind,
    t.flag_dark,
    t.flag_light
FROM tags AS t
LEFT JOIN tag_kinds AS k ON t.kind_id = k.id
ORDER BY t.name;

DROP VIEW IF EXISTS v_items_list;
CREATE VIEW v_items_list AS
SELECT
    i.id,
    i.name,
    i.timing,
    i.kind,
    i.difficulty,
    i.effect,
    i.note,
    i.creation_mana,
    i.entity_strength,
    i.strength,
    i.formula_strength,
    (
        SELECT GROUP_CONCAT(t.name, ', ')
        FROM item_tags AS it
        JOIN tags AS t ON it.tag_id = t.id
        WHERE it.item_id = i.id
    ) AS tag_names
FROM items AS i
ORDER BY i.name;

DROP VIEW IF EXISTS v_weapons_list;
CREATE VIEW v_weapons_list AS
SELECT
    id,
    name,
    recipe,
    cost,
    flavor,
    effect,
    attribute,
    grade,
    weight
FROM weapons
ORDER BY name;

DROP VIEW IF EXISTS v_armor_list;
CREATE VIEW v_armor_list AS
SELECT
    id,
    name,
    recipe,
    cost,
    effect,
    grade,
    weight
FROM armor
ORDER BY name;

DROP VIEW IF EXISTS v_terms_list;
CREATE VIEW v_terms_list AS
SELECT id, name, body, categories
FROM terms
ORDER BY name;

DROP VIEW IF EXISTS v_scorions_list;
CREATE VIEW v_scorions_list AS
SELECT
    id,
    name,
    mana_bias,
    recommended_difficulty,
    enemy_tendency,
    material_tendency,
    adjacency_effect
FROM scorions
ORDER BY name;

DROP VIEW IF EXISTS v_tag_items;
CREATE VIEW v_tag_items AS
SELECT
    t.id AS tag_id,
    t.name AS tag_name,
    i.id AS item_id,
    i.name AS item_name
FROM tags AS t
JOIN item_tags AS it ON it.tag_id = t.id
JOIN items AS i ON it.item_id = i.id
ORDER BY t.name, i.name;
