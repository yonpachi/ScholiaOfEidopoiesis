package part5_test

import (
	"math/rand"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

func part5Dir(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), ".."))
}

func TestBasic4PoolAvgProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	dir := part5Dir(t)
	cmd := exec.Command("go", "run", ".", "-out", outDir, "-seed", "42", "-trials", "100")
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	path := filepath.Join(outDir, "csv", "basic4_pool_avg.csv")
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if len(data) == 0 {
		t.Fatal("empty CSV")
	}
}

func TestScoreByRaceAllRaces(t *testing.T) {
	rng := rand.New(rand.NewSource(99))
	pool := []int{10, 4, 6}
	raw := []dice.Die{{Sides: 10, Face: 5}, {Sides: 4, Face: 2}, {Sides: 6, Face: 3}}
	for race := 0; race < dice.NRaces; race++ {
		_ = dice.ScoreByRace(race, pool, raw, len(pool), rng)
	}
}
