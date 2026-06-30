package main_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

func moduleRoot(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", ".."))
}

func TestMarginalEnumerationProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	root := moduleRoot(t)
	cmd := exec.Command("go", "run", "./sim/part1", "-out", outDir, "-seed", "42", "-trials", "200")
	cmd.Dir = root
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	path := filepath.Join(outDir, "csv", "marginal_by_n.csv")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("missing csv: %v", err)
	}
}
