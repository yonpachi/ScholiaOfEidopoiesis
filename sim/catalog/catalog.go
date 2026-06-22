package catalog

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"
)

const defaultRelativePath = "catalog/game.sqlite"

// Catalog provides read-only access to game content tables.
type Catalog struct {
	db *sql.DB
}

// Open opens a catalog database at path. An empty path uses DefaultPath.
func Open(path string) (*Catalog, error) {
	if path == "" {
		var err error
		path, err = DefaultPath()
		if err != nil {
			return nil, err
		}
	}

	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, fmt.Errorf("open catalog db: %w", err)
	}
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("ping catalog db: %w", err)
	}
	if _, err := db.Exec("PRAGMA foreign_keys = ON"); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("enable foreign keys: %w", err)
	}

	return &Catalog{db: db}, nil
}

// Close releases the database handle.
func (c *Catalog) Close() error {
	if c == nil || c.db == nil {
		return nil
	}
	return c.db.Close()
}

// DB exposes the underlying handle for advanced queries.
func (c *Catalog) DB() *sql.DB {
	return c.db
}

// DefaultPath resolves catalog/game.sqlite from the working directory or parents.
func DefaultPath() (string, error) {
	if env := os.Getenv("CATALOG_PATH"); env != "" {
		return env, nil
	}

	wd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("getwd: %w", err)
	}

	for dir := wd; ; dir = filepath.Dir(dir) {
		candidate := filepath.Join(dir, defaultRelativePath)
		if _, err := os.Stat(candidate); err == nil {
			return candidate, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
	}

	return filepath.Join(wd, defaultRelativePath), nil
}
