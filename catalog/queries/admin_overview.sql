-- Admin overview: row counts per entity table.
SELECT 'tag_kinds' AS entity, COUNT(*) AS rows FROM tag_kinds
UNION ALL SELECT 'marks', COUNT(*) FROM marks
UNION ALL SELECT 'tags', COUNT(*) FROM tags
UNION ALL SELECT 'items', COUNT(*) FROM items
UNION ALL SELECT 'item_tags', COUNT(*) FROM item_tags
UNION ALL SELECT 'weapons', COUNT(*) FROM weapons
UNION ALL SELECT 'armor', COUNT(*) FROM armor
UNION ALL SELECT 'terms', COUNT(*) FROM terms
UNION ALL SELECT 'scorions', COUNT(*) FROM scorions
ORDER BY entity;
