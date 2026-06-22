package main

import (
	"encoding/csv"
	"fmt"
	"math"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"sync/atomic"
	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

// MarginalTable holds per-n_others marginal contribution averages.
type MarginalTable struct {
	Sum [6][dice.MaxN]float64
	Cnt [6][dice.MaxN]int64
}

type pass1Job struct {
	counts [5]int
	d12    int
	idx    int
}

func countPass2Steps() int64 {
	var n int64
	var counts [5]int
	for counts[0] = 0; counts[0] <= dice.MaxN-1; counts[0]++ {
		for counts[1] = 0; counts[1] <= dice.MaxN-1-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= dice.MaxN-1-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= dice.MaxN-1-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= dice.MaxN-1-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						sub := counts[0] + counts[1] + counts[2] + counts[3] + counts[4]
						for d12 := 0; d12 <= 1; d12++ {
							if sub+d12 <= dice.MaxN-1 {
								n++
							}
						}
					}
				}
			}
		}
	}
	return n
}

func collectPass1Jobs() []pass1Job {
	var jobs []pass1Job
	var counts [5]int
	for counts[0] = 0; counts[0] <= dice.MaxN; counts[0]++ {
		for counts[1] = 0; counts[1] <= dice.MaxN-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= dice.MaxN-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= dice.MaxN-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= dice.MaxN-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						for d12 := 0; d12 <= 1; d12++ {
							jobs = append(jobs, pass1Job{
								counts: counts,
								d12:    d12,
								idx:    dice.CacheIdx(counts, d12),
							})
						}
					}
				}
			}
		}
	}
	return jobs
}

func printProgress(prefix string, done, total int64) {
	pct := 100.0 * float64(done) / float64(total)
	fmt.Printf("%s: %d / %d  (%.1f%%)\n", prefix, done, total, pct)
}

// RunFullEnumeration computes marginal contributions and writes marginal_by_n.csv.
func RunFullEnumeration(trialsEnum int, outDir string, baseSeed int64) error {
	cacheSize := dice.Base * dice.Base * dice.Base * dice.Base * dice.Base * 2
	cache := make([]float64, cacheSize)
	for i := range cache {
		cache[i] = math.NaN()
	}

	jobs := collectPass1Jobs()
	nTotal := int64(len(jobs))
	fmt.Printf("  総構成数: %d\n", nTotal)

	var nComputed int64
	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	jobCh := make(chan pass1Job, workers*2)
	var wg sync.WaitGroup

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			var pool [dice.MaxDice]int
			for job := range jobCh {
				subRng := rand.New(rand.NewSource(baseSeed + int64(job.idx)*9973))
				np := dice.BuildPool(job.counts, job.d12 == 1, pool[:])
				stats := dice.SimulatePool(pool[:np], trialsEnum, subRng)
				cache[job.idx] = stats.Avg

				done := atomic.AddInt64(&nComputed, 1)
				if done%100 == 0 || done == nTotal {
					printProgress("PROGRESS1", done, nTotal)
				}
			}
		}()
	}
	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)
	wg.Wait()
	fmt.Printf("\n  キャッシュ完了: %d 構成\n", nTotal)

	var table MarginalTable
	p2Total := countPass2Steps()
	var p2Done int64

	var counts [5]int
	for counts[0] = 0; counts[0] <= dice.MaxN-1; counts[0]++ {
		for counts[1] = 0; counts[1] <= dice.MaxN-1-counts[0]; counts[1]++ {
			for counts[2] = 0; counts[2] <= dice.MaxN-1-counts[0]-counts[1]; counts[2]++ {
				for counts[3] = 1; counts[3] <= dice.MaxN-1-counts[0]-counts[1]-counts[2]; counts[3]++ {
					for counts[4] = 0; counts[4] <= dice.MaxN-1-counts[0]-counts[1]-counts[2]-counts[3]; counts[4]++ {
						sub := counts[0] + counts[1] + counts[2] + counts[3] + counts[4]
						for d12 := 0; d12 <= 1; d12++ {
							total := sub + d12
							if total > dice.MaxN-1 {
								continue
							}
							avgBase := cache[dice.CacheIdx(counts, d12)]
							nOthers := total

							for t := 0; t < 5; t++ {
								counts[t]++
								avgPlus := cache[dice.CacheIdx(counts, d12)]
								counts[t]--
								if math.IsNaN(avgPlus) {
									continue
								}
								diff := avgPlus - avgBase
								table.Sum[t][nOthers] += diff
								table.Cnt[t][nOthers]++
							}
							if d12 == 0 {
								avgPlus := cache[dice.CacheIdx(counts, 1)]
								if !math.IsNaN(avgPlus) {
									diff := avgPlus - avgBase
									table.Sum[5][nOthers] += diff
									table.Cnt[5][nOthers]++
								}
							}

							done := atomic.AddInt64(&p2Done, 1)
							if done%100 == 0 || done == p2Total {
								printProgress("PROGRESS2", done, p2Total)
							}
						}
					}
				}
			}
		}
	}
	fmt.Println("\n  集計完了")

	return writeMarginalCSV(outDir, &table)
}

func writeMarginalCSV(outDir string, table *MarginalTable) error {
	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	path := filepath.Join(csvDir, "marginal_by_n.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	header := make([]string, 7)
	header[0] = "n_others"
	for i, name := range dice.DiceNames {
		header[i+1] = name
	}
	if err := w.Write(header); err != nil {
		return err
	}

	for n := 0; n < dice.MaxN; n++ {
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
