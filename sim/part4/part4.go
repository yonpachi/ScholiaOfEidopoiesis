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
	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

type part4Job struct {
	pool       [dice.MaxDice]int
	nPool      int
	nPoolTotal int
}

type raceAgg struct {
	deltaSumAll       [dice.NRaces]float64
	deltaCntAll       [dice.NRaces]int64
	deltaSumByN       [dice.NRaces][dice.MaxN + 1]float64
	deltaCntByN       [dice.NRaces][dice.MaxN + 1]int64
	useCntByN         [dice.NRaces][dice.MaxN + 1]int64
	usedDeltaSumByN   [dice.NRaces][dice.MaxN + 1]float64
	useCntAll         [dice.NRaces]int64
	usedDeltaSumAll   [dice.NRaces]float64
	homoOptionCnt     [3]int64
	homoOptionCntByN  [3][dice.MaxN + 1]int64
}

func (a *raceAgg) merge(b *raceAgg) {
	for r := 0; r < dice.NRaces; r++ {
		a.deltaSumAll[r] += b.deltaSumAll[r]
		a.deltaCntAll[r] += b.deltaCntAll[r]
		a.useCntAll[r] += b.useCntAll[r]
		a.usedDeltaSumAll[r] += b.usedDeltaSumAll[r]
		for n := 0; n <= dice.MaxN; n++ {
			a.deltaSumByN[r][n] += b.deltaSumByN[r][n]
			a.deltaCntByN[r][n] += b.deltaCntByN[r][n]
			a.useCntByN[r][n] += b.useCntByN[r][n]
			a.usedDeltaSumByN[r][n] += b.usedDeltaSumByN[r][n]
		}
	}
	for o := 0; o < 3; o++ {
		a.homoOptionCnt[o] += b.homoOptionCnt[o]
		for n := 0; n <= dice.MaxN; n++ {
			a.homoOptionCntByN[o][n] += b.homoOptionCntByN[o][n]
		}
	}
}

func collectPart4Jobs() []part4Job {
	var jobs []part4Job
	var counts [5]int
	var pool [dice.MaxDice]int
	for counts[0] = 0; counts[0] <= dice.MaxN; counts[0]++ {
		for counts[1] = 0; counts[1] <= dice.MaxN-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= dice.MaxN-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= dice.MaxN-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= dice.MaxN-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						sub := counts[0] + counts[1] + counts[2] + counts[3] + counts[4]
						for d12 := 0; d12 <= 1; d12++ {
							nPoolTotal := sub + d12
							if nPoolTotal < 2 || nPoolTotal > dice.MaxN {
								continue
							}
							np := dice.BuildPool(counts, d12 == 1, pool[:])
							var job part4Job
							job.nPool = np
							job.nPoolTotal = nPoolTotal
							copy(job.pool[:np], pool[:np])
							jobs = append(jobs, job)
						}
					}
				}
			}
		}
	}
	return jobs
}

func simulatePart4Job(job part4Job, trials int, rng *rand.Rand) raceAgg {
	var agg raceAgg
	var sumDelta [dice.NRaces]float64
	var sumUsed [dice.NRaces]int64
	var sumUsedDelta [dice.NRaces]float64
	var sumHomo [3]int64

	pool := job.pool[:job.nPool]
	var diceRaw [dice.MaxDice]dice.Die

	for tr := 0; tr < trials; tr++ {
		nRaw := job.nPool
		for i := 0; i < job.nPool; i++ {
			diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
		}
		base := dice.BaselineFromRaw(diceRaw[:], nRaw, rng)

		s, used := dice.ScoreHuman(diceRaw[:], nRaw, rng)
		sumDelta[0] += float64(s - base)
		if used {
			sumUsed[0]++
			sumUsedDelta[0] += float64(s - base)
		}

		s = dice.ScoreMakina(pool, rng)
		d := float64(s - base)
		sumDelta[1] += d
		sumUsed[1]++
		sumUsedDelta[1] += d

		s, used = dice.ScoreBeast(diceRaw[:], nRaw, rng)
		sumDelta[2] += float64(s - base)
		if used {
			sumUsed[2]++
			sumUsedDelta[2] += float64(s - base)
		}

		s, opt := dice.ScoreHomunculus(diceRaw[:], nRaw, rng)
		sumDelta[3] += float64(s - base)
		if opt >= 0 {
			sumHomo[opt]++
			sumUsed[3]++
			sumUsedDelta[3] += float64(s - base)
		}

		s, used = dice.ScoreRelicia(diceRaw[:], nRaw, rng)
		sumDelta[4] += float64(s - base)
		if used {
			sumUsed[4]++
			sumUsedDelta[4] += float64(s - base)
		}

		s, used = dice.ScoreUmbra(diceRaw[:], nRaw, rng)
		sumDelta[5] += float64(s - base)
		if used {
			sumUsed[5]++
			sumUsedDelta[5] += float64(s - base)
		}
	}

	n := job.nPoolTotal
	for r := 0; r < dice.NRaces; r++ {
		avgD := sumDelta[r] / float64(trials)
		agg.deltaSumAll[r] += avgD
		agg.deltaCntAll[r] = 1
		agg.deltaSumByN[r][n] += avgD
		agg.deltaCntByN[r][n] = 1
		agg.useCntByN[r][n] += sumUsed[r]
		agg.usedDeltaSumByN[r][n] += sumUsedDelta[r]
		agg.useCntAll[r] += sumUsed[r]
		agg.usedDeltaSumAll[r] += sumUsedDelta[r]
	}
	for o := 0; o < 3; o++ {
		agg.homoOptionCnt[o] += sumHomo[o]
		agg.homoOptionCntByN[o][n] += sumHomo[o]
	}
	return agg
}

// RunRaceAbilityComparison enumerates pools and compares race abilities (Part4).
func RunRaceAbilityComparison(trialsPerPool int, outDir string, baseSeed int64) error {
	jobs := collectPart4Jobs()
	nTotal := int64(len(jobs))
	fmt.Printf("  総構成数: %d\n", nTotal)

	var done int64
	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	jobCh := make(chan part4Job, workers*2)
	var wg sync.WaitGroup
	var mu sync.Mutex
	var totalAgg raceAgg

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(baseSeed + int64(workerID)*99991))
			for job := range jobCh {
				local := simulatePart4Job(job, trialsPerPool, rng)
				mu.Lock()
				totalAgg.merge(&local)
				mu.Unlock()
				d := atomic.AddInt64(&done, 1)
				if d%100 == 0 || d == nTotal {
					fmt.Printf("PROGRESS4: %d / %d  (%.1f%%)\n", d, nTotal, 100.0*float64(d)/float64(nTotal))
				}
			}
		}(w)
	}
	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)
	wg.Wait()

	fmt.Println()
	fmt.Println("============================================================")
	fmt.Printf("  Part4: 六種族 判定時効果 強さ比較（全構成列挙）\n")
	fmt.Printf("  trials/pool=%d, max_pool=%d\n", trialsPerPool, dice.MaxN)
	fmt.Println("  ※ d10>=1固定、d12は0-1個、全有効構成の平均を表示")
	fmt.Println("============================================================")
	fmt.Printf("%-14s  avg_delta  use_rate  delta|use   sample_count\n", "種族")
	fmt.Println("--------------  ---------  --------  ----------  ------------")

	raceNamesJP := [dice.NRaces]string{"人間", "機械人", "獣人", "ホムンクルス", "付喪B(入替)", "半霊"}
	for r := 0; r < dice.NRaces; r++ {
		avg := 0.0
		if totalAgg.deltaCntAll[r] > 0 {
			avg = totalAgg.deltaSumAll[r] / float64(totalAgg.deltaCntAll[r])
		}
		ttotal := totalAgg.deltaCntAll[r] * int64(trialsPerPool)
		useRate := 0.0
		if ttotal > 0 {
			useRate = float64(totalAgg.useCntAll[r]) / float64(ttotal)
		}
		deltaGivenUse := 0.0
		if totalAgg.useCntAll[r] > 0 {
			deltaGivenUse = totalAgg.usedDeltaSumAll[r] / float64(totalAgg.useCntAll[r])
		}
		fmt.Printf("%-14s  %+9.4f  %7.1f%%  %+10.4f  %12d\n",
			raceNamesJP[r], avg, useRate*100, deltaGivenUse, totalAgg.deltaCntAll[r])
	}

	homoTotal := totalAgg.homoOptionCnt[0] + totalAgg.homoOptionCnt[1] + totalAgg.homoOptionCnt[2]
	if homoTotal > 0 {
		fmt.Println("\nホムンクルス三択選択率:")
		homoNames := [3]string{"A(全-1→0)", "B(反応数÷2)", "C(変異)"}
		for o := 0; o < 3; o++ {
			fmt.Printf("  %-14s : %6d  (%.1f%%)\n", homoNames[o], totalAgg.homoOptionCnt[o],
				100.0*float64(totalAgg.homoOptionCnt[o])/float64(homoTotal))
		}
	}

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	if err := writeRaceCSV(csvDir, totalAgg, trialsPerPool, homoTotal); err != nil {
		return err
	}
	return nil
}

func writeRaceCSV(outDir string, agg raceAgg, trialsPerPool int, homoTotal int64) error {
	if err := writeRaceMatrixCSV(filepath.Join(outDir, "race_ability_by_n.csv"), agg, trialsPerPool, func(r, n int) (float64, bool) {
		if agg.deltaCntByN[r][n] == 0 {
			return 0, false
		}
		return agg.deltaSumByN[r][n] / float64(agg.deltaCntByN[r][n]), true
	}); err != nil {
		return err
	}
	fmt.Printf("\nCSV output: %s\n", filepath.Join(outDir, "race_ability_by_n.csv"))

	usePath := filepath.Join(outDir, "race_use_rate_by_n.csv")
	if err := writeRaceMatrixCSV(usePath, agg, trialsPerPool, func(r, n int) (float64, bool) {
		total := agg.deltaCntByN[r][n] * int64(trialsPerPool)
		if total == 0 {
			return 0, false
		}
		return float64(agg.useCntByN[r][n]) / float64(total), true
	}); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", usePath)

	deltaPath := filepath.Join(outDir, "race_delta_use_by_n.csv")
	if err := writeRaceMatrixCSV(deltaPath, agg, trialsPerPool, func(r, n int) (float64, bool) {
		if agg.useCntByN[r][n] == 0 {
			return 0, false
		}
		return agg.usedDeltaSumByN[r][n] / float64(agg.useCntByN[r][n]), true
	}); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", deltaPath)

	homoPath := filepath.Join(outDir, "homunculus_option_distribution.csv")
	hf, err := os.Create(homoPath)
	if err != nil {
		return err
	}
	w := csv.NewWriter(hf)
	_ = w.Write([]string{"option", "count", "rate"})
	homoCSVNames := [3]string{"A(all_neg_to_0)", "B(reacted_div2)", "C(mutation)"}
	for o := 0; o < 3; o++ {
		rate := 0.0
		if homoTotal > 0 {
			rate = float64(agg.homoOptionCnt[o]) / float64(homoTotal)
		}
		_ = w.Write([]string{homoCSVNames[o], fmt.Sprintf("%d", agg.homoOptionCnt[o]), fmt.Sprintf("%.4f", rate)})
	}
	w.Flush()
	hf.Close()
	if err := w.Error(); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", homoPath)

	byNPath := filepath.Join(outDir, "homunculus_option_by_n.csv")
	bf, err := os.Create(byNPath)
	if err != nil {
		return err
	}
	w2 := csv.NewWriter(bf)
	_ = w2.Write([]string{"n_pool", "A_rate", "B_rate", "C_rate"})
	for n := 1; n <= dice.MaxN; n++ {
		totalN := agg.homoOptionCntByN[0][n] + agg.homoOptionCntByN[1][n] + agg.homoOptionCntByN[2][n]
		row := []string{fmt.Sprintf("%d", n)}
		for o := 0; o < 3; o++ {
			rate := 0.0
			if totalN > 0 {
				rate = float64(agg.homoOptionCntByN[o][n]) / float64(totalN)
			}
			row = append(row, fmt.Sprintf("%.4f", rate))
		}
		_ = w2.Write(row)
	}
	w2.Flush()
	bf.Close()
	fmt.Printf("CSV output: %s\n", byNPath)
	return w2.Error()
}

func writeRaceMatrixCSV(path string, agg raceAgg, _ int, cell func(r, n int) (float64, bool)) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	header := []string{"n_pool"}
	for r := 0; r < dice.NRaces; r++ {
		header = append(header, dice.RaceNamesCSV[r])
	}
	if err := w.Write(header); err != nil {
		return err
	}
	for n := 1; n <= dice.MaxN; n++ {
		row := []string{fmt.Sprintf("%d", n)}
		for r := 0; r < dice.NRaces; r++ {
			if v, ok := cell(r, n); ok {
				row = append(row, fmt.Sprintf("%.4f", v))
			} else {
				row = append(row, "")
			}
		}
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	return w.Error()
}
