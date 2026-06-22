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

const MaxExtraBasic4 = 9

// Basic4Sides are elemental dice used in Part5 (Fire/Earth/Wind/Water).
var Basic4Sides = [4]int{4, 6, 8, 20}

// RunBasic4PoolAvg simulates 1d10 + N random basic-4 dice with random race per trial.
func RunBasic4PoolAvg(trials int, outDir string, seed int64) error {
	rng := rand.New(rand.NewSource(seed))

	fmt.Println()
	fmt.Println("============================================================")
	fmt.Println("  Part5: 1d10(固定) + N×ランダム基本4ダイス 合計達成値")
	fmt.Println("  基本4ダイス = {d4(火), d6(地), d8(風), d20(水)}")
	fmt.Println("  各試行: ダイス構成・種族ともにランダム選択")
	fmt.Println("  反応ルール＋種族能力(最大利得)を適用")
	fmt.Printf("  trials=%d,  N=0~%d\n", trials, MaxExtraBasic4)
	fmt.Println("============================================================")
	fmt.Printf("%-10s  %10s  %8s  %8s  %8s\n", "n_extra", "avg", "p50", "p90", "p99")
	fmt.Println("----------  ----------  --------  --------  --------")

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	path := filepath.Join(csvDir, "basic4_pool_avg.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	if err := w.Write([]string{"n_extra", "avg", "p50", "p90", "p99"}); err != nil {
		return err
	}

	var pool [dice.MaxDice]int
	var diceRaw [dice.MaxDice]dice.Die

	for nExtra := 0; nExtra <= MaxExtraBasic4; nExtra++ {
		totals := make([]int, trials)
		nPool := 1 + nExtra
		pool[0] = 10
		for t := 0; t < trials; t++ {
			for i := 0; i < nExtra; i++ {
				pool[1+i] = Basic4Sides[rng.Intn(4)]
			}
			for i := 0; i < nPool; i++ {
				diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
			}
			race := rng.Intn(dice.NRaces)
			totals[t] = dice.ScoreByRace(race, pool[:nPool], diceRaw[:], nPool, rng)
		}

		sort.Ints(totals)
		sum := 0.0
		for _, v := range totals {
			sum += float64(v)
		}
		avg := sum / float64(trials)
		p50 := totals[int(0.50*float64(trials-1))]
		p90 := totals[int(0.90*float64(trials-1))]
		p99 := totals[int(0.99*float64(trials-1))]

		fmt.Printf("%10d  %10.3f  %8d  %8d  %8d\n", nExtra, avg, p50, p90, p99)
		if err := w.Write([]string{
			fmt.Sprintf("%d", nExtra),
			fmt.Sprintf("%.4f", avg),
			fmt.Sprintf("%d", p50),
			fmt.Sprintf("%d", p90),
			fmt.Sprintf("%d", p99),
		}); err != nil {
			return err
		}
		fmt.Printf("PROGRESS5: %d / %d\n", nExtra+1, MaxExtraBasic4+1)
	}

	w.Flush()
	if err := w.Error(); err != nil {
		return err
	}
	fmt.Printf("\nCSV output: %s\n", path)
	return nil
}
