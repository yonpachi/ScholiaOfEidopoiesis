package catalog

import (
	"database/sql"
	"fmt"
)

// Mark is a named effect category (印記).
type Mark struct {
	ID     string
	Name   string
	Effect string
	Decay  string
}

// MarkByName returns a mark by display name.
func (c *Catalog) MarkByName(name string) (Mark, error) {
	row := c.db.QueryRow(
		`SELECT id, name, effect, decay FROM marks WHERE name = ?`,
		name,
	)
	var m Mark
	if err := row.Scan(&m.ID, &m.Name, &m.Effect, &m.Decay); err != nil {
		if err == sql.ErrNoRows {
			return Mark{}, fmt.Errorf("mark not found: %s", name)
		}
		return Mark{}, err
	}
	return m, nil
}

// AllMarks returns every mark ordered by name.
func (c *Catalog) AllMarks() ([]Mark, error) {
	rows, err := c.db.Query(
		`SELECT id, name, effect, decay FROM marks ORDER BY name`,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Mark
	for rows.Next() {
		var m Mark
		if err := rows.Scan(&m.ID, &m.Name, &m.Effect, &m.Decay); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

// AllMarkNames returns mark display names.
func (c *Catalog) AllMarkNames() ([]string, error) {
	rows, err := c.db.Query(`SELECT name FROM marks ORDER BY name`)
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

// MarkNameSet returns mark names as a set for membership checks.
func (c *Catalog) MarkNameSet() (map[string]struct{}, error) {
	names, err := c.AllMarkNames()
	if err != nil {
		return nil, err
	}
	set := make(map[string]struct{}, len(names))
	for _, name := range names {
		set[name] = struct{}{}
	}
	return set, nil
}
