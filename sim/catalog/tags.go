package catalog

import (
	"database/sql"
	"fmt"
)

// Tag is a material/flavor classification on items.
type Tag struct {
	ID     string
	Name   string
	Mana   string
	KindID sql.NullString
	Effect string
}

// TagByName returns a tag by display name.
func (c *Catalog) TagByName(name string) (Tag, error) {
	row := c.db.QueryRow(
		`SELECT id, name, mana, kind_id, effect FROM tags WHERE name = ?`,
		name,
	)
	var t Tag
	if err := row.Scan(&t.ID, &t.Name, &t.Mana, &t.KindID, &t.Effect); err != nil {
		if err == sql.ErrNoRows {
			return Tag{}, fmt.Errorf("tag not found: %s", name)
		}
		return Tag{}, err
	}
	return t, nil
}

// AllTagNames returns tag display names.
func (c *Catalog) AllTagNames() ([]string, error) {
	rows, err := c.db.Query(`SELECT name FROM tags ORDER BY name`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []string
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return nil, err
		}
		out = append(out, name)
	}
	return out, rows.Err()
}

// TagsForItem returns tags linked to an item by item id.
func (c *Catalog) TagsForItem(itemID string) ([]Tag, error) {
	rows, err := c.db.Query(
		`
		SELECT t.id, t.name, t.mana, t.kind_id, t.effect
		FROM tags AS t
		JOIN item_tags AS it ON it.tag_id = t.id
		WHERE it.item_id = ?
		ORDER BY t.name
		`,
		itemID,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Tag
	for rows.Next() {
		var t Tag
		if err := rows.Scan(&t.ID, &t.Name, &t.Mana, &t.KindID, &t.Effect); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// TagsForItemName returns tags linked to an item by display name.
func (c *Catalog) TagsForItemName(itemName string) ([]Tag, error) {
	var itemID string
	err := c.db.QueryRow(`SELECT id FROM items WHERE name = ?`, itemName).Scan(&itemID)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("item not found: %s", itemName)
		}
		return nil, err
	}
	return c.TagsForItem(itemID)
}
