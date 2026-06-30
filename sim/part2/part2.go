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

type part2Job struct {
	pool       [dice.MaxDice]int
	nPool      int
	nPoolTotal int
}

type raceAgg struct {
	deltaSumAll      [ancestry.NRaces]float64
	deltaCntAll      [ancestry.NRaces]int64
	deltaSumByN      [ancestry.NRaces][dice.MaxN + 1]float64
	deltaCntByN      [ancestry.NRaces][dice.MaxN + 1]int64
	useCntByN        [ancestry.NRaces][dice.MaxN + 1]int64
	usedDeltaSumByN  [ancestry.NRaces][dice.MaxN + 1]float64
	useCntAll        [ancestry.NRaces]int64
	usedDeltaSumAll  [ancestry.NRaces]float64
	homoOptionCnt    [3]int64
	homoOptionCntByN [3][dice.MaxN + 1]int64
}

func (a *raceAgg) merge(b *raceAgg) {
	for r := 0; r < ancestry.NRaces; r++ {
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

func collectPart2Jobs() []part2Job {
	var jobs []part2Job
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
					var job part2Job
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

func simulatePart2Job(job part2Job, trials int, rng *rand.Rand) raceAgg {
	var agg raceAgg
	var sumDelta [ancestry.NRaces]float64
	var sumUsed [ancestry.NRaces]int64
	var sumUsedDelta [ancestry.NRaces]float64
	var sumHomo [3]int64

	pool := job.pool[:job.nPool]
	var diceRaw [dice.MaxDice]dice.Die

	for tr := 0; tr < trials; tr++ {
		for i := 0; i < job.nPool; i++ {
			diceRaw[i] = dice.Die{Sides: pool[i], Face: rng.Intn(pool[i]) + 1}
		}
		base := dice.BaselineFromRaw(diceRaw[:], job.nPool, rng)

		s, used := ancestry.ScoreHuman(diceRaw[:], job.nPool, rng)
		sumDelta[0] += float64(s - base)
		if used {
			sumUsed[0]++
			sumUsedDelta[0] += float64(s - base)
		}

		s = ancestry.ScoreMakina(pool, rng)
		d := float64(s - base)
		sumDelta[1] += d
		sumUsed[1]++
		sumUsedDelta[1] += d

		s, used = ancestry.ScoreBeast(diceRaw[:], job.nPool, rng)
		sumDelta[2] += float64(s - base)
		if used {
			sumUsed[2]++
			sumUsedDelta[2] += float64(s - base)
		}

		s, opt := ancestry.ScoreHomunculus(diceRaw[:], job.nPool, rng)
		sumDelta[3] += float64(s - base)
		if opt >= 0 {
			sumHomo[opt]++
			sumUsed[3]++
			sumUsedDelta[3] += float64(s - base)
		}

		s, used = ancestry.ScoreRelicia(diceRaw[:], job.nPool, rng)
		sumDelta[4] += float64(s - base)
		if used {
			sumUsed[4]++
			sumUsedDelta[4] += float64(s - base)
		}

		s, used = ancestry.ScoreUmbra(diceRaw[:], job.nPool, rng)
		sumDelta[5] += float64(s - base)
		if used {
			sumUsed[5]++
			sumUsedDelta[5] += float64(s - base)
		}
	}

	n := job.nPoolTotal
	for r := 0; r < ancestry.NRaces; r++ {
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

func printSummary(agg *raceAgg, trialsPerPool int) {
	fmt.Println()
	fmt.Println("============================================================")
	fmt.Println("  Part2: 六種族 判定時効果 強さ比較（全構成列挙）")
	fmt.Printf("  trials/pool=%d, max_pool=%d\n", trialsPerPool, dice.MaxN)
	fmt.Println("  ※ ベースd10固定、レシピはd4/d6/d8/d20のみ、全有効構成の平均を表示")
	fmt.Println("============================================================")
	fmt.Printf("%-14s  avg_delta  use_rate  delta|use   sample_count\n", "種族")
	fmt.Println("--------------  ---------  --------  ----------  ------------")

	raceNamesJP := [ancestry.NRaces]string{"人間", "機巧", "獣裔", "ホムンクルス", "付喪", "半霊"}
	for r := 0; r < ancestry.NRaces; r++ {
		avg := 0.0
		if agg.deltaCntAll[r] > 0 {
			avg = agg.deltaSumAll[r] / float64(agg.deltaCntAll[r])
		}
		ttotal := agg.deltaCntAll[r] * int64(trialsPerPool)
		useRate := 0.0
		if ttotal > 0 {
			useRate = float64(agg.useCntAll[r]) / float64(ttotal)
		}
		deltaGivenUse := 0.0
		if agg.useCntAll[r] > 0 {
			deltaGivenUse = agg.usedDeltaSumAll[r] / float64(agg.useCntAll[r])
		}
		fmt.Printf("%-14s  %+9.4f  %7.1f%%  %+10.4f  %12d\n",
			raceNamesJP[r], avg, useRate*100, deltaGivenUse, agg.deltaCntAll[r])
	}

	homoTotal := agg.homoOptionCnt[0] + agg.homoOptionCnt[1] + agg.homoOptionCnt[2]
	if homoTotal > 0 {
		fmt.Println("\nホムンクルス三択選択率:")
		homoNames := [3]string{"修正", "発現", "変異"}
		for o := 0; o < 3; o++ {
			fmt.Printf("  %-14s : %6d  (%.1f%%)\n", homoNames[o], agg.homoOptionCnt[o],
				100.0*float64(agg.homoOptionCnt[o])/float64(homoTotal))
		}
	}
}

// RunRaceAbilityComparison enumerates pools and compares race abilities.
func RunRaceAbilityComparison(trialsPerPool int, outDir string, baseSeed int64) error {
	jobs := collectPart2Jobs()
	nTotal := int64(len(jobs))
	fmt.Printf("  総構成数: %d\n", nTotal)

	var done int64
	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	jobCh := make(chan part2Job, workers*2)
	var wg sync.WaitGroup
	var mu sync.Mutex
	var totalAgg raceAgg

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(baseSeed + int64(workerID)*99991))
			for job := range jobCh {
				local := simulatePart2Job(job, trialsPerPool, rng)
				mu.Lock()
				totalAgg.merge(&local)
				mu.Unlock()
				d := atomic.AddInt64(&done, 1)
				if d%100 == 0 || d == nTotal {
					fmt.Printf("PROGRESS2: %d / %d  (%.1f%%)\n", d, nTotal, 100.0*float64(d)/float64(nTotal))
				}
			}
		}(w)
	}
	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)
	wg.Wait()

	printSummary(&totalAgg, trialsPerPool)

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	return writeRaceCSV(csvDir, &totalAgg, trialsPerPool)
}

func writeRaceCSV(outDir string, agg *raceAgg, trialsPerPool int) error {
	homoTotal := agg.homoOptionCnt[0] + agg.homoOptionCnt[1] + agg.homoOptionCnt[2]

	byN := filepath.Join(outDir, "race_ability_by_n.csv")
	if err := writeRaceMatrixCSV(byN, agg, trialsPerPool, func(r, n int) (float64, bool) {
		if agg.deltaCntByN[r][n] == 0 {
			return 0, false
		}
		return agg.deltaSumByN[r][n] / float64(agg.deltaCntByN[r][n]), true
	}); err != nil {
		return err
	}
	fmt.Printf("\nCSV output: %s\n", byN)

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
	if err := writeHomunculusDistCSV(homoPath, agg, homoTotal); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", homoPath)

	byNPath := filepath.Join(outDir, "homunculus_option_by_n.csv")
	if err := writeHomunculusByNCSV(byNPath, agg); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", byNPath)
	return nil
}

func writeRaceMatrixCSV(path string, agg *raceAgg, _ int, cell func(r, n int) (float64, bool)) (err error) {
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
	header := []string{"n_pool"}
	for r := 0; r < ancestry.NRaces; r++ {
		header = append(header, ancestry.RaceNamesCSV[r])
	}
	if err := w.Write(header); err != nil {
		return err
	}
	for n := 1; n <= dice.MaxN; n++ {
		row := []string{fmt.Sprintf("%d", n)}
		for r := 0; r < ancestry.NRaces; r++ {
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

func writeHomunculusDistCSV(path string, agg *raceAgg, homoTotal int64) (err error) {
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
	if err := w.Write([]string{"option", "count", "rate"}); err != nil {
		return err
	}
	names := [3]string{"fix", "manifest", "mutate"}
	for o := 0; o < 3; o++ {
		rate := 0.0
		if homoTotal > 0 {
			rate = float64(agg.homoOptionCnt[o]) / float64(homoTotal)
		}
		if err := w.Write([]string{names[o], fmt.Sprintf("%d", agg.homoOptionCnt[o]), fmt.Sprintf("%.4f", rate)}); err != nil {
			return err
		}
	}
	w.Flush()
	return w.Error()
}

func writeHomunculusByNCSV(path string, agg *raceAgg) (err error) {
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
	if err := w.Write([]string{"n_pool", "fix_rate", "manifest_rate", "mutate_rate"}); err != nil {
		return err
	}
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
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	return w.Error()
}
