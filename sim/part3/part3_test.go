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

func TestRaceScoreComparisonProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	root := repoRoot(t)
	cmd := exec.Command("go", "run", "./sim/part3", "-out", outDir, "-seed", "42", "-trials", "20")
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	csvPath := filepath.Join(outDir, "csv", "race_score_by_n.csv")
	if _, err := os.Stat(csvPath); err != nil {
		t.Fatalf("missing race_score_by_n.csv: %v\noutput:\n%s", err, out)
	}
}
