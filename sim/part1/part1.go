package main

import (
	"encoding/csv"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

// RefDice lists dice types for Part1 reference (name aligned with sides).
var RefDice = []struct {
	Name  string
	Sides int
}{
	{"d4", 4},
	{"d6", 6},
	{"d8", 8},
	{"d10", 10},
	{"d12", 12},
	{"d20", 20},
}

// RunPart1Reference prints single-die x5 reference stats and optionally writes CSV.
func RunPart1Reference(trials int, outDir string, rng *rand.Rand) error {
	fmt.Printf("=== Part1: single die x5 reference (trials=%d) ===\n", trials)
	fmt.Printf("%-6s  avg/die  p50/die  p90/die  p99/die\n", "pool")
	fmt.Printf("------  -------  -------  -------  -------\n")

	type row struct {
		name            string
		avg, p50, p90, p99 float64
	}
	rows := make([]row, 0, len(RefDice))

	for _, ref := range RefDice {
		pool := make([]int, 5)
		for i := range pool {
			pool[i] = ref.Sides
		}
		stats := dice.SimulatePool(pool, trials, rng)
		r := row{
			name: ref.Name,
			avg:  stats.Avg / 5.0,
			p50:  float64(stats.P50) / 5.0,
			p90:  float64(stats.P90) / 5.0,
			p99:  float64(stats.P99) / 5.0,
		}
		rows = append(rows, r)
		fmt.Printf("%-6s  %7.3f  %7.1f  %7.1f  %7.1f\n",
			r.name, r.avg, r.p50, r.p90, r.p99)
	}

	if outDir == "" {
		return nil
	}
	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	path := filepath.Join(csvDir, "part1_reference.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write([]string{"dice", "avg_per_die", "p50_per_die", "p90_per_die", "p99_per_die"}); err != nil {
		return err
	}
	for _, r := range rows {
		if err := w.Write([]string{
			r.name,
			fmt.Sprintf("%.4f", r.avg),
			fmt.Sprintf("%.1f", r.p50),
			fmt.Sprintf("%.1f", r.p90),
			fmt.Sprintf("%.1f", r.p99),
		}); err != nil {
			return err
		}
	}
	w.Flush()
	fmt.Printf("CSV output: %s\n", path)
	return w.Error()
}
