package part2_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

func part2Dir(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), ".."))
}

func TestMarginalEnumerationProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	dir := part2Dir(t)
	cmd := exec.Command("go", "run", ".", "-out", outDir, "-seed", "42", "-trials", "500")
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	path := filepath.Join(outDir, "csv", "marginal_by_n.csv")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("missing csv: %v", err)
	}
}
