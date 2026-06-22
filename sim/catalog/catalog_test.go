package catalog_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/catalog"
)

func repoCatalogPath(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	for dir := wd; ; dir = filepath.Dir(dir) {
		candidate := filepath.Join(dir, "catalog", "game.sqlite")
		if _, err := os.Stat(candidate); err == nil {
			return candidate
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Fatal("catalog/game.sqlite not found from test working directory")
		}
	}
}

func TestOpenAndMarks(t *testing.T) {
	path := repoCatalogPath(t)
	cat, err := catalog.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer cat.Close()

	mark, err := cat.MarkByName("毒")
	if err != nil {
		t.Fatal(err)
	}
	if mark.Decay != "発動時減衰" {
		t.Fatalf("unexpected decay: %q", mark.Decay)
	}

	names, err := cat.AllMarkNames()
	if err != nil {
		t.Fatal(err)
	}
	if len(names) < 20 {
		t.Fatalf("expected at least 20 marks, got %d", len(names))
	}
}

func TestTagsForItemName(t *testing.T) {
	path := repoCatalogPath(t)
	cat, err := catalog.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer cat.Close()

	tags, err := cat.TagsForItemName("失敗作")
	if err != nil {
		t.Fatal(err)
	}
	if len(tags) != 1 || tags[0].Name != "真っ黒" {
		t.Fatalf("unexpected tags: %+v", tags)
	}
}

func TestValidateCatalog(t *testing.T) {
	path := repoCatalogPath(t)
	cat, err := catalog.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer cat.Close()

	issues := cat.Validate()
	for _, issue := range issues {
		t.Errorf("%s", issue.Error())
	}
}
