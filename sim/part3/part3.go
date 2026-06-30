package main

import (
	"encoding/csv"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"sync/atomic"

	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/ancestry"
	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/dice"
)

const (
	idxBaseline = 0
	idxRaceMean = 7
	nSeries     = 8
)

type part3Job struct {
	pool       [dice.MaxDice]int
	nPool      int
	nPoolTotal int
}

type scoreAgg struct {
	sumByN [nSeries][dice.MaxN + 1]float64
	cntByN [dice.MaxN + 1]int64
}

func (a *scoreAgg) merge(b *scoreAgg) {
	for s := 0; s < nSeries; s++ {
		for n := 0; n <= dice.MaxN; n++ {
			a.sumByN[s][n] += b.sumByN[s][n]
		}
	}
	for n := 0; n <= dice.MaxN; n++ {
		a.cntByN[n] += b.cntByN[n]
	}
}

func collectPart3Jobs() []part3Job {
	var jobs []part3Job
	var counts [4]int
	var pool [dice.MaxDice]int
	for counts[0] = 0; counts[0] <= dice.MaxN-1; counts[0]++ {
		for counts[1] = 0; counts[1] <= dice.MaxN-1-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= dice.MaxN-1-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 0; counts[3] <= dice.MaxN-1-counts[0]-counts[1]-counts[2]; counts[3]++ {
					nAttr := counts[0] + counts[1] + counts[2] + counts[3]
					if nAttr < 1 || 1+nAttr > dice.MaxN {
						continue
					}
					np := dice.BuildRecipePool(counts, pool[:])
					var job part3Job
					job.nPool = np
					job.nPoolTotal = np
					copy(job.pool[:np], pool[:np])
					jobs = append(jobs, job)
				}
			}
		}
	}
	return jobs
}

func simulatePart3Job(job part3Job, trials int, rng *rand.Rand) scoreAgg {
	var agg scoreAgg
	var sum [nSeries]float64

	pool := job.pool[:job.nPool]
	var diceRaw [dice.MaxDice]dice.Die

	for tr := 0; tr < trials; tr++ {
		for i := 0; i < job.nPool; i++ {
			diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
		}

		base := dice.BaselineFromRaw(diceRaw[:], job.nPool, rng)
		sum[idxBaseline] += float64(base)

		s0, _ := ancestry.ScoreHuman(diceRaw[:], job.nPool, rng)
		sum[1] += float64(s0)

		s1 := ancestry.ScoreMakina(pool, rng)
		sum[2] += float64(s1)

		s2, _ := ancestry.ScoreBeast(diceRaw[:], job.nPool, rng)
		sum[3] += float64(s2)

		s3, _ := ancestry.ScoreHomunculus(diceRaw[:], job.nPool, rng)
		sum[4] += float64(s3)

		s4, _ := ancestry.ScoreRelicia(diceRaw[:], job.nPool, rng)
		sum[5] += float64(s4)

		s5, _ := ancestry.ScoreUmbra(diceRaw[:], job.nPool, rng)
		sum[6] += float64(s5)

		trialMean := float64(s0+s1+s2+s3+s4+s5) / float64(ancestry.NRaces)
		sum[idxRaceMean] += trialMean
	}

	n := job.nPoolTotal
	ft := float64(trials)
	for s := 0; s < nSeries; s++ {
		agg.sumByN[s][n] += sum[s] / ft
	}
	agg.cntByN[n] = 1
	return agg
}

func printSummary(agg *scoreAgg) {
	fmt.Println()
	fmt.Println("============================================================")
	fmt.Println("  Part3: 六種族 判定時平均スコア（全構成列挙）")
	fmt.Println("  ※ ベースd10固定、レシピはd4/d6/d8/d20のみ、全有効構成の平均を表示")
	fmt.Println("============================================================")

	seriesNames := [nSeries]string{
		"種族なし", "人間", "機巧", "獣裔", "ホムンクルス", "付喪", "半霊", "種族平均",
	}
	fmt.Printf("%-14s", "系列")
	for n := 1; n <= dice.MaxN; n++ {
		fmt.Printf("  n=%-2d", n)
	}
	fmt.Println()
	fmt.Println("--------------" + repeatDash(6*dice.MaxN))

	for s := 0; s < nSeries; s++ {
		fmt.Printf("%-14s", seriesNames[s])
		for n := 1; n <= dice.MaxN; n++ {
			if agg.cntByN[n] == 0 {
				fmt.Printf("  %4s", "-")
				continue
			}
			avg := agg.sumByN[s][n] / float64(agg.cntByN[n])
			fmt.Printf("  %4.1f", avg)
		}
		fmt.Println()
	}
}

func repeatDash(n int) string {
	b := make([]byte, n)
	for i := range b {
		b[i] = '-'
	}
	return string(b)
}

// RunRaceScoreComparison enumerates recipe pools and averages race scores.
func RunRaceScoreComparison(trialsPerPool int, outDir string, baseSeed int64) error {
	jobs := collectPart3Jobs()
	nTotal := int64(len(jobs))
	fmt.Printf("  総構成数: %d\n", nTotal)
	fmt.Printf("  trials/pool=%d, max_pool=%d\n", trialsPerPool, dice.MaxN)

	var done int64
	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	jobCh := make(chan part3Job, workers*2)
	var wg sync.WaitGroup
	var mu sync.Mutex
	var totalAgg scoreAgg

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(baseSeed + int64(workerID)*99991))
			for job := range jobCh {
				local := simulatePart3Job(job, trialsPerPool, rng)
				mu.Lock()
				totalAgg.merge(&local)
				mu.Unlock()
				d := atomic.AddInt64(&done, 1)
				if d%100 == 0 || d == nTotal {
					fmt.Printf("PROGRESS3: %d / %d  (%.1f%%)\n", d, nTotal, 100.0*float64(d)/float64(nTotal))
				}
			}
		}(w)
	}
	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)
	wg.Wait()

	printSummary(&totalAgg)

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	return writeScoreCSV(csvDir, &totalAgg)
}

func writeScoreCSV(outDir string, agg *scoreAgg) error {
	path := filepath.Join(outDir, "race_score_by_n.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer func() {
		if cerr := f.Close(); cerr != nil && err == nil {
			err = cerr
		}
	}()

	w := csv.NewWriter(f)
	header := []string{"n_pool", "Baseline"}
	for r := 0; r < ancestry.NRaces; r++ {
		header = append(header, ancestry.RaceNamesCSV[r])
	}
	header = append(header, "RaceMean")
	if err := w.Write(header); err != nil {
		return err
	}

	for n := 1; n <= dice.MaxN; n++ {
		if agg.cntByN[n] == 0 {
			continue
		}
		row := []string{fmt.Sprintf("%d", n)}
		for s := 0; s < nSeries; s++ {
			avg := agg.sumByN[s][n] / float64(agg.cntByN[n])
			row = append(row, fmt.Sprintf("%.4f", avg))
		}
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return err
	}
	fmt.Printf("\nCSV output: %s\n", path)
	return nil
}
