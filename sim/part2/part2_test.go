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

func TestRaceAbilityComparisonProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	root := repoRoot(t)
	cmd := exec.Command("go", "run", "./sim/part2", "-out", outDir, "-seed", "42", "-trials", "20")
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	for _, name := range []string{
		"race_ability_by_n.csv",
		"race_use_rate_by_n.csv",
		"race_delta_use_by_n.csv",
		"homunculus_option_distribution.csv",
		"homunculus_option_by_n.csv",
	} {
		if _, err := os.Stat(filepath.Join(outDir, "csv", name)); err != nil {
			t.Fatalf("missing %s: %v\noutput:\n%s", name, err, out)
		}
	}
}
