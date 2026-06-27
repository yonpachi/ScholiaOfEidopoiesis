package part6_test

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

func part6Dir(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), ".."))
}

func TestQualityProgressionProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	dir := part6Dir(t)
	cmd := exec.Command("go", "run", ".", "-out", outDir, "-seed", "42", "-trials", "20")
	cmd.Dir = dir
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go run: %v\n%s", err, out)
	}
	csvPath := filepath.Join(outDir, "csv", "quality_progression.csv")
	if _, err := os.Stat(csvPath); err != nil {
		t.Fatalf("missing quality_progression.csv: %v", err)
	}

	f, err := os.Open(csvPath)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()

	rows, err := csv.NewReader(f).ReadAll()
	if err != nil {
		t.Fatal(err)
	}
	wantRows := (12 * 10) + 1 // n_extra 1..12 × attempt 1..10 + header
	if len(rows) != wantRows {
		t.Fatalf("got %d rows, want %d", len(rows), wantRows)
	}
}

func TestCampaignQualityInvariants(t *testing.T) {
	rng := rand.New(rand.NewSource(12345))
	pool := []int{10, 6}
	race := 0
	nPool := len(pool)

	saved := 0
	prevQuality := 0
	for attempt := 1; attempt <= 10; attempt++ {
		var diceRaw [dice.MaxDice]dice.Die
		for i := 0; i < nPool; i++ {
			diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
		}
		roll := dice.ScoreByRace(race, pool, diceRaw[:], nPool, rng)
		if roll > saved {
			saved = roll
		}
		quality := attempt + saved
		if quality < attempt {
			t.Fatalf("attempt %d: quality %d < attempt", attempt, quality)
		}
		if attempt > 1 && quality <= prevQuality {
			t.Fatalf("attempt %d: quality %d not greater than previous %d", attempt, quality, prevQuality)
		}
		prevQuality = quality
	}
}
