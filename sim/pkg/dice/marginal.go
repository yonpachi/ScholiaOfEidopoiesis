package dice

import (
	"encoding/csv"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
)

func cacheIdx(counts [5]int, d12 int) int {
	idx := counts[0]
	for i := 1; i < 5; i++ {
		idx = idx*Base + counts[i]
	}
	return idx + d12*(Base*Base*Base*Base*Base)
}

func buildPool(counts [5]int, hasD12 bool, pool []int) int {
	np := 0
	for t := 0; t < 5; t++ {
		for k := 0; k < counts[t]; k++ {
			pool[np] = DiceSides[t]
			np++
		}
	}
	if hasD12 {
		pool[np] = 12
		np++
	}
	return np
}

// MarginalTable holds per-n_others marginal contribution averages.
type MarginalTable struct {
	Sum [6][MaxN]float64
	Cnt [6][MaxN]int64
}

// RunFullEnumeration computes marginal contributions and writes marginal_by_n.csv.
func RunFullEnumeration(trialsEnum int, wind WindMode, outDir string, rng *rand.Rand) error {
	cacheSize := Base * Base * Base * Base * Base * 2
	cache := make([]float64, cacheSize)
	for i := range cache {
		cache[i] = math.NaN()
	}

	var counts [5]int
	var pool [MaxDice]int
	nComputed := int64(0)

	for counts[0] = 0; counts[0] <= MaxN; counts[0]++ {
		for counts[1] = 0; counts[1] <= MaxN-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= MaxN-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= MaxN-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= MaxN-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						for d12 := 0; d12 <= 1; d12++ {
							idx := cacheIdx(counts, d12)
							np := buildPool(counts, d12 == 1, pool[:])
							stats := SimulatePool(pool[:np], trialsEnum, wind, rng)
							cache[idx] = stats.Avg
							nComputed++
						}
					}
				}
			}
		}
	}
	fmt.Printf("  cache complete: %d compositions\n", nComputed)

	var table MarginalTable

	for counts[0] = 0; counts[0] <= MaxN-1; counts[0]++ {
		for counts[1] = 0; counts[1] <= MaxN-1-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= MaxN-1-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= MaxN-1-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= MaxN-1-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						sub := counts[0] + counts[1] + counts[2] + counts[3] + counts[4]
						for d12 := 0; d12 <= 1; d12++ {
							total := sub + d12
							if total > MaxN-1 {
								continue
							}
							avgBase := cache[cacheIdx(counts, d12)]
							nOthers := total

							for t := 0; t < 5; t++ {
								counts[t]++
								avgPlus := cache[cacheIdx(counts, d12)]
								counts[t]--
								if math.IsNaN(avgPlus) {
									continue
								}
								diff := avgPlus - avgBase
								table.Sum[t][nOthers] += diff
								table.Cnt[t][nOthers]++
							}
							if d12 == 0 {
								avgPlus := cache[cacheIdx(counts, 1)]
								if !math.IsNaN(avgPlus) {
									diff := avgPlus - avgBase
									table.Sum[5][nOthers] += diff
									table.Cnt[5][nOthers]++
								}
							}
						}
					}
				}
			}
		}
	}

	return writeMarginalCSV(outDir, &table)
}

func writeMarginalCSV(outDir string, table *MarginalTable) error {
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return err
	}
	path := filepath.Join(outDir, "marginal_by_n.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	header := make([]string, 7)
	header[0] = "n_others"
	for i, name := range DiceNames {
		header[i+1] = name
	}
	if err := w.Write(header); err != nil {
		return err
	}

	for n := 0; n < MaxN; n++ {
		row := make([]string, 7)
		row[0] = fmt.Sprintf("%d", n)
		for t := 0; t < 6; t++ {
			if table.Cnt[t][n] > 0 {
				row[t+1] = fmt.Sprintf("%.4f", table.Sum[t][n]/float64(table.Cnt[t][n]))
			}
		}
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	fmt.Printf("CSV output: %s\n", path)
	return w.Error()
}

// RunPart1Reference prints single-die reference stats (console only).
func RunPart1Reference(trials int, wind WindMode, rng *rand.Rand) {
	fmt.Printf("=== Part1: single die x5 reference (trials=%d) ===\n", trials)
	fmt.Printf("%-6s  avg/die  p50/die  p90/die  p99/die\n", "pool")
	fmt.Printf("------  -------  -------  -------  -------\n")

	refSides := []int{4, 6, 8, 10, 12, 20}
	refNames := DiceNames[:]
	for t, sides := range refSides {
		pool := make([]int, 5)
		for i := range pool {
			pool[i] = sides
		}
		stats := SimulatePool(pool, trials, wind, rng)
		fmt.Printf("%-6s  %7.3f  %7.1f  %7.1f  %7.1f\n",
			refNames[t], stats.Avg/5.0,
			float64(stats.P50)/5.0, float64(stats.P90)/5.0, float64(stats.P99)/5.0)
	}
}
