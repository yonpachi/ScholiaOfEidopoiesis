package main

import (
	"encoding/csv"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"sort"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

const (
	MinExtraBasic4   = 1
	MaxExtraBasic4   = 12
	CampaignAttempts = 10
)

// Basic4Sides are elemental dice used in Part6 (Fire/Earth/Wind/Water).
var Basic4Sides = [4]int{4, 6, 8, 20}

func percentile(sorted []int, p float64) int {
	if len(sorted) == 0 {
		return 0
	}
	if len(sorted) == 1 {
		return sorted[0]
	}
	idx := int(p * float64(len(sorted)-1))
	if idx < 0 {
		idx = 0
	}
	if idx >= len(sorted) {
		idx = len(sorted) - 1
	}
	return sorted[idx]
}

func rollAchievement(race int, pool []int, nPool int, rng *rand.Rand) int {
	var diceRaw [dice.MaxDice]dice.Die
	for i := 0; i < nPool; i++ {
		diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
	}
	return dice.ScoreByRace(race, pool, diceRaw[:], nPool, rng)
}

// RunQualityProgression simulates repeated alchemy campaigns and records quality at each attempt.
func RunQualityProgression(trials int, outDir string, seed int64) error {
	rng := rand.New(rand.NewSource(seed))

	fmt.Println()
	fmt.Println("============================================================")
	fmt.Println("  Part6: 品質成長（10回連続錬金）")
	fmt.Println("  1d10(固定) + N×基本4ダイス、キャンペーン内で種族・プール固定")
	fmt.Println("  品質 = 熟練度 + 保存錬金値（max採用）")
	fmt.Printf("  trials=%d,  N=%d~%d,  attempts=%d\n", trials, MinExtraBasic4, MaxExtraBasic4, CampaignAttempts)
	fmt.Println("============================================================")
	fmt.Printf("%-8s %-8s %8s %8s %8s\n", "n_extra", "attempt", "p50", "p90", "p99")
	fmt.Println("-------- -------- -------- -------- --------")

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	path := filepath.Join(csvDir, "quality_progression.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write([]string{"n_extra", "attempt", "p50", "p90", "p99"}); err != nil {
		return err
	}

	var pool [dice.MaxDice]int

	for nExtra := MinExtraBasic4; nExtra <= MaxExtraBasic4; nExtra++ {
		nPool := 1 + nExtra
		qualities := make([][]int, CampaignAttempts)
		for a := 0; a < CampaignAttempts; a++ {
			qualities[a] = make([]int, trials)
		}

		for t := 0; t < trials; t++ {
			pool[0] = 10
			for i := 0; i < nExtra; i++ {
				pool[1+i] = Basic4Sides[rng.Intn(4)]
			}
			race := rng.Intn(dice.NRaces)
			poolSlice := pool[:nPool]

			saved := 0
			for attempt := 1; attempt <= CampaignAttempts; attempt++ {
				roll := rollAchievement(race, poolSlice, nPool, rng)
				if roll > saved {
					saved = roll
				}
				qualities[attempt-1][t] = attempt + saved
			}
		}

		for attempt := 1; attempt <= CampaignAttempts; attempt++ {
			sorted := qualities[attempt-1]
			sort.Ints(sorted)
			p50 := percentile(sorted, 0.50)
			p90 := percentile(sorted, 0.90)
			p99 := percentile(sorted, 0.99)

			fmt.Printf("%8d %8d %8d %8d %8d\n", nExtra, attempt, p50, p90, p99)
			if err := w.Write([]string{
				fmt.Sprintf("%d", nExtra),
				fmt.Sprintf("%d", attempt),
				fmt.Sprintf("%d", p50),
				fmt.Sprintf("%d", p90),
				fmt.Sprintf("%d", p99),
			}); err != nil {
				return err
			}
		}
		fmt.Printf("PROGRESS6: %d / %d\n", nExtra-MinExtraBasic4+1, MaxExtraBasic4-MinExtraBasic4+1)
	}

	w.Flush()
	if err := w.Error(); err != nil {
		return err
	}
	fmt.Printf("\nCSV output: %s\n", path)
	return nil
}
