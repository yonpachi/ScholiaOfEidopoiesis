package part3_test

import (
	"encoding/csv"
	"math/rand"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

func part3Dir(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), ".."))
}

func TestSimulateSuccessRateBounds(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	pool := []int{10}
	rate := dice.SimulateSuccessRate(pool, 5000, 1, rng)
	if rate < 0.85 || rate > 1.0 {
		t.Errorf("d10only target=1 success rate = %.3f, want ~0.9", rate)
	}
	rateHigh := dice.SimulateSuccessRate(pool, 5000, 20, rng)
	if rateHigh > 0.05 {
		t.Errorf("d10only target=20 success rate = %.3f, want near 0", rateHigh)
	}
}

func TestDifficultyTableProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	dir := part3Dir(t)
	cmd := exec.Command("go", "run", ".", "-out", outDir, "-seed", "42", "-trials", "500")
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	path := filepath.Join(outDir, "csv", "difficulty_table.csv")
	f, err := os.Open(path)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	rows, err := csv.NewReader(f).ReadAll()
	if err != nil {
		t.Fatal(err)
	}
	if len(rows) != 26 {
		t.Errorf("got %d rows, want 26", len(rows))
	}
}
