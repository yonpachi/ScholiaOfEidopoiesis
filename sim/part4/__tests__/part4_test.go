package part4_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

func part4Dir(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), ".."))
}

func TestRaceAbilityComparisonProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	dir := part4Dir(t)
	cmd := exec.Command("go", "run", ".", "-out", outDir, "-seed", "42", "-trials", "20")
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
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
			t.Fatalf("missing %s: %v", name, err)
		}
	}
}
