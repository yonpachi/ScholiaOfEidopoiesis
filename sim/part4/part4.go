package main

import (
	"encoding/csv"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"sync"
	"sync/atomic"

	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/dice"
)

const (
	nWeights       = 3
	nBands         = 4
	refWeight      = 1 // 中量
	refBand        = 1 // 中行動
	defaultMaxK    = 10
	defaultTrashHP = 20
	gradeMin       = 1
	gradeMax       = 20
)

var weightNames = [nWeights]string{"軽量", "中量", "重量"}
var bandNames = [nBands]string{"軽行動", "中行動", "重行動", "特行動"}

// 攻撃の待機値（左）と攻撃係数（右）。backup/balance/constants.yaml の武器表。
var weaponWait = [nWeights][nBands]int{
	{2, 3, 4, 5},
	{3, 4, 5, 6},
	{4, 5, 6, 7},
}
var weaponCoef = [nWeights][nBands]int{
	{3, 4, 4, 5},
	{3, 6, 6, 7},
	{4, 6, 8, 11},
}

type kStats struct {
	avg   float64
	p50   int
	p99   int
	reach float64
}

func dpcRatio(wi, bi int) float64 {
	return float64(weaponCoef[wi][bi]) / float64(weaponWait[wi][bi])
}

func percentile(sorted []int, p float64) int {
	if len(sorted) == 0 {
		return 0
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

// prefixMax は独立錬金の達成値列から、その時点までの最良品質を返す。
func prefixMax(vals []int) []int {
	out := make([]int, len(vals))
	best := 0
	for i, v := range vals {
		if i == 0 || v > best {
			best = v
		}
		out[i] = best
	}
	return out
}

// weaponHit は錬価×係数。錬価＝⌊品質÷等級⌋。
func weaponHit(quality, grade, coef int) int {
	if grade < 1 || coef < 1 {
		return 0
	}
	return (quality / grade) * coef
}

// hitsToKill は切り上げ。ダメージ0は倒せないので 0 を返す。
func hitsToKill(hp, dmg int) int {
	if dmg <= 0 || hp <= 0 {
		return 0
	}
	return (hp + dmg - 1) / dmg
}

func firstKAtLeast(vals []float64, target float64) int {
	for i, v := range vals {
		if v >= target {
			return i + 1
		}
	}
	return 0
}

// collectRecipeCounts は余剰 nAttr 個を d4/d6/d8/d20 へ配る全構成（構成は均等重み）。
func collectRecipeCounts(nAttr int) [][4]int {
	if nAttr < 0 {
		nAttr = 0
	}
	var out [][4]int
	var counts [4]int
	var rec func(i, left int)
	rec = func(i, left int) {
		if i == 3 {
			counts[3] = left
			var c [4]int
			copy(c[:], counts[:])
			out = append(out, c)
			return
		}
		for v := 0; v <= left; v++ {
			counts[i] = v
			rec(i+1, left-v)
		}
	}
	rec(0, nAttr)
	return out
}

func poolsForN(nPool int) [][]int {
	nAttr := nPool - 1
	countsList := collectRecipeCounts(nAttr)
	pools := make([][]int, 0, len(countsList))
	var buf [dice.MaxDice]int
	for _, c := range countsList {
		np := dice.BuildRecipePool(c, buf[:])
		p := make([]int, np)
		copy(p, buf[:np])
		pools = append(pools, p)
	}
	return pools
}

func rollCraftPool(pool []int, rng *rand.Rand) int {
	np := len(pool)
	var diceRaw [dice.MaxDice]dice.Die
	for i := 0; i < np; i++ {
		sides := pool[i]
		diceRaw[i] = dice.Die{Sides: sides, Face: rng.Intn(sides) + 1}
	}
	return dice.BaselineFromRaw(diceRaw[:], np, rng)
}

func simulateNPool(nPool, trials, maxK, trashHP int, rng *rand.Rand) []kStats {
	pools := poolsForN(nPool)
	best := make([][]int, maxK)
	for k := 0; k < maxK; k++ {
		best[k] = make([]int, trials)
	}
	for tr := 0; tr < trials; tr++ {
		pool := pools[rng.Intn(len(pools))]
		m := 0
		for k := 0; k < maxK; k++ {
			q := rollCraftPool(pool, rng)
			if q > m {
				m = q
			}
			best[k][tr] = m
		}
	}
	rows := make([]kStats, maxK)
	for k := 0; k < maxK; k++ {
		reachN := 0
		sum := 0.0
		for _, v := range best[k] {
			sum += float64(v)
			if v >= trashHP {
				reachN++
			}
		}
		sort.Ints(best[k])
		rows[k] = kStats{
			avg:   sum / float64(trials),
			p50:   percentile(best[k], 0.50),
			p99:   percentile(best[k], 0.99),
			reach: float64(reachN) / float64(trials),
		}
	}
	return rows
}

// RunQualityAttempts は各マナについて、再錬金 k 回の最良品質を集計する。
// レシピ構成は均等重み。セッション内は同一構成。種族なし。
func RunQualityAttempts(trials, maxK, trashHP int, outDir string, baseSeed int64) error {
	if trials < 1 {
		trials = 1
	}
	if maxK < 1 {
		maxK = 1
	}
	if trashHP < 1 {
		trashHP = defaultTrashHP
	}

	fmt.Printf("  trials=%d, maxK=%d, 雑魚HP=%d\n", trials, maxK, trashHP)
	fmt.Printf("  レシピ構成は均等重み。セッション内は同一構成を k 回振って最良を採用（種族なし）\n")
	fmt.Printf("  規準セル: %s × %s  待機=%d 係数=%d\n",
		weightNames[refWeight], bandNames[refBand],
		weaponWait[refWeight][refBand], weaponCoef[refWeight][refBand])

	workers := runtime.NumCPU()
	if workers < 1 {
		workers = 1
	}
	nCh := make(chan int, dice.MaxN)
	for n := 1; n <= dice.MaxN; n++ {
		nCh <- n
	}
	close(nCh)

	table := make([][]kStats, dice.MaxN+1)
	var mu sync.Mutex
	var wg sync.WaitGroup
	var done int64
	nTotal := int64(dice.MaxN)

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			rng := rand.New(rand.NewSource(baseSeed + int64(workerID)*99991))
			for nPool := range nCh {
				rows := simulateNPool(nPool, trials, maxK, trashHP, rng)
				mu.Lock()
				table[nPool] = rows
				mu.Unlock()
				d := atomic.AddInt64(&done, 1)
				fmt.Printf("PROGRESS4: %d / %d  (%.1f%%)\n", d, nTotal, 100.0*float64(d)/float64(nTotal))
			}
		}(w)
	}
	wg.Wait()

	printSummary(table, maxK, trashHP)
	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	return writePart4CSV(csvDir, table, maxK, trashHP)
}

func manaOf(nPool int) int {
	return nPool - 1
}

func pickP50(s kStats) float64 { return float64(s.p50) }
func pickAvg(s kStats) float64 { return s.avg }

func kSeries(table [][]kStats, mana, maxK int, pick func(kStats) float64) []float64 {
	nPool := mana + 1
	out := make([]float64, maxK)
	if nPool < 1 || nPool >= len(table) || table[nPool] == nil {
		return out
	}
	for k := 0; k < maxK && k < len(table[nPool]); k++ {
		out[k] = pick(table[nPool][k])
	}
	return out
}

func printKOrNever(k int) string {
	if k < 1 {
		return "未到達"
	}
	return fmt.Sprintf("k=%d", k)
}

func printSummary(table [][]kStats, maxK, trashHP int) {
	fmt.Println()
	fmt.Println("============================================================")
	fmt.Println("  Part4: 品質 × 再錬金回数（最良を採用）")
	fmt.Println("============================================================")
	fmt.Printf("%-6s %-4s %8s %6s %6s %10s\n", "マナ", "k", "avg", "p50", "p99", "P>=雑魚")
	for nPool := 1; nPool <= dice.MaxN; nPool++ {
		rows := table[nPool]
		if len(rows) == 0 {
			continue
		}
		for k, r := range rows {
			fmt.Printf("%-6d %-4d %8.2f %6d %6d %10.3f\n",
				manaOf(nPool), k+1, r.avg, r.p50, r.p99, r.reach)
		}
	}
	fmt.Println()
	fmt.Println("雑魚HP到達（2マナ／3マナ）:")
	for _, mana := range []int{2, 3} {
		kAvg := firstKAtLeast(kSeries(table, mana, maxK, pickAvg), float64(trashHP))
		kP50 := firstKAtLeast(kSeries(table, mana, maxK, pickP50), float64(trashHP))
		kReach := firstKAtLeast(kSeries(table, mana, maxK, func(s kStats) float64 { return s.reach }), 0.5)
		fmt.Printf("  %dマナ  avg>=%d: %s  p50>=%d: %s  P>=%d at 50%%: %s\n",
			mana, trashHP, printKOrNever(kAvg), trashHP, printKOrNever(kP50), trashHP, printKOrNever(kReach))
	}

	q2 := qualityRef(table, 2, 1)
	q3 := qualityRef(table, 3, 1)
	kStar := firstKAtLeast(kSeries(table, 2, maxK, pickP50), float64(trashHP))
	q2s := q2
	if kStar > 0 {
		q2s = qualityRef(table, 2, kStar)
	} else {
		q2s = qualityRef(table, 2, maxK)
	}
	coef := weaponCoef[refWeight][refBand]
	fmt.Println()
	fmt.Printf("代表品質: 2マナ k=1 p50=%d  2マナ鍛錬 p50=%d (%s)  3マナ k=1 p50=%d\n",
		q2, q2s, printKOrNever(kStar), q3)
	fmt.Println("中量中 1撃 (floor(Q/G)*係数):")
	fmt.Printf("  %-4s %8s %8s %8s %10s %8s\n", "等級", "錬価", "1撃", "雑魚撃数", "PC_HP(5撃)", "Q=")
	for _, g := range []int{5, 7, 8, 9, 10, 12, 15} {
		renka := 0
		if g > 0 {
			renka = q2 / g
		}
		hit := weaponHit(q2, g, coef)
		fmt.Printf("  %-4d %8d %8d %8d %10d %8d\n",
			g, renka, hit, hitsToKill(trashHP, hit), 5*hit, q2)
	}
}

func qualityRef(table [][]kStats, mana, k int) int {
	nPool := mana + 1
	if nPool < 1 || nPool >= len(table) || table[nPool] == nil {
		return 0
	}
	if k < 1 || k > len(table[nPool]) {
		return 0
	}
	return table[nPool][k-1].p50
}

func writePart4CSV(outDir string, table [][]kStats, maxK, trashHP int) error {
	if err := writeLongCSV(filepath.Join(outDir, "quality_by_mana_k.csv"), table, maxK); err != nil {
		return err
	}
	if err := writeWideCSV(filepath.Join(outDir, "quality_avg_by_k.csv"), table, maxK, func(s kStats) float64 { return s.avg }); err != nil {
		return err
	}
	if err := writeWideCSV(filepath.Join(outDir, "quality_p50_by_k.csv"), table, maxK, func(s kStats) float64 { return float64(s.p50) }); err != nil {
		return err
	}
	if err := writeWideCSV(filepath.Join(outDir, "quality_p99_by_k.csv"), table, maxK, func(s kStats) float64 { return float64(s.p99) }); err != nil {
		return err
	}
	if err := writeWideCSV(filepath.Join(outDir, "quality_reach_by_k.csv"), table, maxK, func(s kStats) float64 { return s.reach }); err != nil {
		return err
	}
	if err := writeReachCSV(filepath.Join(outDir, "trash_reach_k.csv"), table, maxK, trashHP); err != nil {
		return err
	}
	return writeGradeCSV(filepath.Join(outDir, "weapon_grade.csv"), table, maxK, trashHP)
}

func writeCSV(path string, fn func(*csv.Writer) error) error {
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
	if err := fn(w); err != nil {
		return err
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return err
	}
	fmt.Printf("CSV output: %s\n", path)
	return nil
}

func writeLongCSV(path string, table [][]kStats, maxK int) error {
	return writeCSV(path, func(w *csv.Writer) error {
		if err := w.Write([]string{"n_pool", "mana", "k", "avg", "p50", "p99", "reach_trash"}); err != nil {
			return err
		}
		for nPool := 1; nPool <= dice.MaxN; nPool++ {
			rows := table[nPool]
			for k := 0; k < maxK && k < len(rows); k++ {
				r := rows[k]
				if err := w.Write([]string{
					fmt.Sprintf("%d", nPool),
					fmt.Sprintf("%d", manaOf(nPool)),
					fmt.Sprintf("%d", k+1),
					fmt.Sprintf("%.4f", r.avg),
					fmt.Sprintf("%d", r.p50),
					fmt.Sprintf("%d", r.p99),
					fmt.Sprintf("%.4f", r.reach),
				}); err != nil {
					return err
				}
			}
		}
		return nil
	})
}

func writeWideCSV(path string, table [][]kStats, maxK int, pick func(kStats) float64) error {
	return writeCSV(path, func(w *csv.Writer) error {
		header := []string{"k"}
		for nPool := 1; nPool <= dice.MaxN; nPool++ {
			header = append(header, fmt.Sprintf("マナ%d", manaOf(nPool)))
		}
		if err := w.Write(header); err != nil {
			return err
		}
		for k := 0; k < maxK; k++ {
			row := []string{fmt.Sprintf("%d", k+1)}
			for nPool := 1; nPool <= dice.MaxN; nPool++ {
				val := ""
				if table[nPool] != nil && k < len(table[nPool]) {
					val = fmt.Sprintf("%.4f", pick(table[nPool][k]))
				}
				row = append(row, val)
			}
			if err := w.Write(row); err != nil {
				return err
			}
		}
		return nil
	})
}

func writeReachCSV(path string, table [][]kStats, maxK, trashHP int) error {
	return writeCSV(path, func(w *csv.Writer) error {
		if err := w.Write([]string{"mana", "k_avg_ge_trash", "k_p50_ge_trash", "k_p99_ge_trash", "k_reach50"}); err != nil {
			return err
		}
		for nPool := 1; nPool <= dice.MaxN; nPool++ {
			mana := manaOf(nPool)
			kAvg := firstKAtLeast(kSeries(table, mana, maxK, pickAvg), float64(trashHP))
			kP50 := firstKAtLeast(kSeries(table, mana, maxK, pickP50), float64(trashHP))
			kP99 := firstKAtLeast(kSeries(table, mana, maxK, func(s kStats) float64 { return float64(s.p99) }), float64(trashHP))
			kReach := firstKAtLeast(kSeries(table, mana, maxK, func(s kStats) float64 { return s.reach }), 0.5)
			if err := w.Write([]string{
				fmt.Sprintf("%d", mana),
				fmt.Sprintf("%d", kAvg),
				fmt.Sprintf("%d", kP50),
				fmt.Sprintf("%d", kP99),
				fmt.Sprintf("%d", kReach),
			}); err != nil {
				return err
			}
		}
		return nil
	})
}

func writeGradeCSV(path string, table [][]kStats, maxK, trashHP int) error {
	q2 := qualityRef(table, 2, 1)
	q3 := qualityRef(table, 3, 1)
	kStar := firstKAtLeast(kSeries(table, 2, maxK, pickP50), float64(trashHP))
	q2s := qualityRef(table, 2, maxK)
	if kStar > 0 {
		q2s = qualityRef(table, 2, kStar)
	}
	coef := weaponCoef[refWeight][refBand]
	return writeCSV(path, func(w *csv.Writer) error {
		header := []string{
			"等級",
			"Q2k1", "錬価_Q2k1", "1撃_Q2k1", "雑魚撃数_Q2k1", "PC_HP5_Q2k1",
			"Q2鍛", "k_star", "錬価_Q2鍛", "1撃_Q2鍛", "雑魚撃数_Q2鍛",
			"Q3k1", "錬価_Q3k1", "1撃_Q3k1", "雑魚撃数_Q3k1",
		}
		if err := w.Write(header); err != nil {
			return err
		}
		for g := gradeMin; g <= gradeMax; g++ {
			h2 := weaponHit(q2, g, coef)
			h2s := weaponHit(q2s, g, coef)
			h3 := weaponHit(q3, g, coef)
			if err := w.Write([]string{
				fmt.Sprintf("%d", g),
				fmt.Sprintf("%d", q2),
				fmt.Sprintf("%d", q2/g),
				fmt.Sprintf("%d", h2),
				fmt.Sprintf("%d", hitsToKill(trashHP, h2)),
				fmt.Sprintf("%d", 5*h2),
				fmt.Sprintf("%d", q2s),
				fmt.Sprintf("%d", kStar),
				fmt.Sprintf("%d", q2s/g),
				fmt.Sprintf("%d", h2s),
				fmt.Sprintf("%d", hitsToKill(trashHP, h2s)),
				fmt.Sprintf("%d", q3),
				fmt.Sprintf("%d", q3/g),
				fmt.Sprintf("%d", h3),
				fmt.Sprintf("%d", hitsToKill(trashHP, h3)),
			}); err != nil {
				return err
			}
		}
		return nil
	})
}
