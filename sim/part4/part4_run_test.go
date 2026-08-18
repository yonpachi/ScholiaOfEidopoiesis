package main_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

func repoRoot(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", ".."))
}

func TestQualityAttemptsProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	root := repoRoot(t)
	cmd := exec.Command(
		"go", "run", "./sim/part4",
		"-out", outDir,
		"-seed", "42",
		"-trials", "20",
		"-maxk", "4",
		"-trash", "20",
	)
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	want := []string{
		"quality_by_mana_k.csv",
		"quality_avg_by_k.csv",
		"quality_p50_by_k.csv",
		"quality_p99_by_k.csv",
		"quality_reach_by_k.csv",
		"trash_reach_k.csv",
		"weapon_grade.csv",
	}
	for _, name := range want {
		path := filepath.Join(outDir, "csv", name)
		if _, err := os.Stat(path); err != nil {
			t.Fatalf("missing %s: %v\noutput:\n%s", name, err, out)
		}
	}
}
