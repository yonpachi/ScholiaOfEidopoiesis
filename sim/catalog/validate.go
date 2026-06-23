package catalog

import (
	"fmt"
	"regexp"
	"strings"
)

var markRefPattern = regexp.MustCompile(`<([^<>]+)>`)

// ValidationIssue describes a catalog consistency problem.
type ValidationIssue struct {
	Rule    string
	Message string
}

func (v ValidationIssue) Error() string {
	return fmt.Sprintf("[%s] %s", v.Rule, v.Message)
}

// Validate checks catalog invariants documented in legacy/marks_and_tags.md.
func (c *Catalog) Validate() []ValidationIssue {
	var issues []ValidationIssue
	issues = append(issues, c.validateUniqueNames()...)
	issues = append(issues, c.validateTagMarkNameCollision()...)
	issues = append(issues, c.validateItemTagFK()...)
	issues = append(issues, c.validateMarkReferencesInEffects()...)
	return issues
}

func (c *Catalog) validateUniqueNames() []ValidationIssue {
	var issues []ValidationIssue
	for _, check := range []struct {
		rule  string
		table string
	}{
		{"unique_mark_name", "marks"},
		{"unique_tag_name", "tags"},
		{"unique_item_name", "items"},
		{"unique_weapon_name", "weapons"},
		{"unique_armor_name", "armor"},
	} {
		rows, err := c.db.Query(
			fmt.Sprintf(
				`SELECT name, COUNT(*) AS n FROM %s GROUP BY name HAVING n > 1`,
				check.table,
			),
		)
		if err != nil {
			issues = append(issues, ValidationIssue{
				Rule:    check.rule,
				Message: err.Error(),
			})
			continue
		}
		for rows.Next() {
			var name string
			var count int
			if err := rows.Scan(&name, &count); err != nil {
				issues = append(issues, ValidationIssue{Rule: check.rule, Message: err.Error()})
				continue
			}
			issues = append(issues, ValidationIssue{
				Rule:    check.rule,
				Message: fmt.Sprintf("duplicate %s name %q (%d rows)", check.table, name, count),
			})
		}
		rows.Close()
	}
	return issues
}

func (c *Catalog) validateTagMarkNameCollision() []ValidationIssue {
	rows, err := c.db.Query(
		`
		SELECT t.name
		FROM tags AS t
		INNER JOIN marks AS m ON m.name = t.name
		ORDER BY t.name
		`,
	)
	if err != nil {
		return []ValidationIssue{{Rule: "tag_mark_collision", Message: err.Error()}}
	}
	defer rows.Close()

	var issues []ValidationIssue
	for rows.Next() {
		var name string
		if err := rows.Scan(&name); err != nil {
			return []ValidationIssue{{Rule: "tag_mark_collision", Message: err.Error()}}
		}
		issues = append(issues, ValidationIssue{
			Rule:    "tag_mark_collision",
			Message: fmt.Sprintf("name %q used by both tag and mark", name),
		})
	}
	return issues
}

func (c *Catalog) validateItemTagFK() []ValidationIssue {
	rows, err := c.db.Query(
		`
		SELECT it.item_id, it.tag_id
		FROM item_tags AS it
		LEFT JOIN items AS i ON i.id = it.item_id
		LEFT JOIN tags AS t ON t.id = it.tag_id
		WHERE i.id IS NULL OR t.id IS NULL
		`,
	)
	if err != nil {
		return []ValidationIssue{{Rule: "item_tag_fk", Message: err.Error()}}
	}
	defer rows.Close()

	var issues []ValidationIssue
	for rows.Next() {
		var itemID, tagID string
		if err := rows.Scan(&itemID, &tagID); err != nil {
			return []ValidationIssue{{Rule: "item_tag_fk", Message: err.Error()}}
		}
		issues = append(issues, ValidationIssue{
			Rule:    "item_tag_fk",
			Message: fmt.Sprintf("broken link item_id=%q tag_id=%q", itemID, tagID),
		})
	}
	return issues
}

func (c *Catalog) validateMarkReferencesInEffects() []ValidationIssue {
	markSet, err := c.MarkNameSet()
	if err != nil {
		return []ValidationIssue{{Rule: "mark_reference", Message: err.Error()}}
	}

	type source struct {
		kind string
		name string
		text string
	}
	var sources []source

	appendQuery := func(kind, query string) []ValidationIssue {
		rows, err := c.db.Query(query)
		if err != nil {
			return []ValidationIssue{{Rule: "mark_reference", Message: err.Error()}}
		}
		defer rows.Close()
		for rows.Next() {
			var name, text string
			if err := rows.Scan(&name, &text); err != nil {
				return []ValidationIssue{{Rule: "mark_reference", Message: err.Error()}}
			}
			sources = append(sources, source{kind: kind, name: name, text: text})
		}
		return nil
	}

	for _, issue := range appendQuery("weapon", `SELECT name, effect FROM weapons`) {
		return []ValidationIssue{issue}
	}
	for _, issue := range appendQuery("armor", `SELECT name, effect FROM armor`) {
		return []ValidationIssue{issue}
	}
	for _, issue := range appendQuery("item", `SELECT name, effect FROM items`) {
		return []ValidationIssue{issue}
	}

	var issues []ValidationIssue
	for _, src := range sources {
		for _, ref := range markRefPattern.FindAllStringSubmatch(src.text, -1) {
			refName := strings.TrimSpace(ref[1])
			if refName == "" {
				continue
			}
			if _, ok := markSet[refName]; !ok {
				issues = append(issues, ValidationIssue{
					Rule: "mark_reference",
					Message: fmt.Sprintf(
						"%s %q references unknown mark <%s>",
						src.kind, src.name, refName,
					),
				})
			}
		}
	}
	return issues
}
