-- Tags not linked to any item (informational; tags may legitimately have no items yet).
SELECT t.id, t.name, t.kind_id
FROM tags AS t
LEFT JOIN item_tags AS it ON it.tag_id = t.id
WHERE it.item_id IS NULL
ORDER BY t.name;
