package main

import (
	"encoding/csv"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

const (
	TargetMin = 1
	TargetMax = 25
)

// DifficultyCombo is a pool for Part3 success-rate table.
type DifficultyCombo struct {
	Name string
	Pool []int
}

// DifficultyCombos lists 1d10 + optional elemental die pools.
var DifficultyCombos = []DifficultyCombo{
	{Name: "d10only", Pool: []int{10}},
	{Name: "d10+d4(Fire)", Pool: []int{10, 4}},
	{Name: "d10+d6(Earth)", Pool: []int{10, 6}},
	{Name: "d10+d8(Wind)", Pool: []int{10, 8}},
	{Name: "d10+d20(Water)", Pool: []int{10, 20}},
}

// RunDifficultyTable computes success rates by target and writes difficulty_table.csv.
func RunDifficultyTable(trials int, outDir string, seed int64) error {
	rng := rand.New(rand.NewSource(seed))

	fmt.Println()
	fmt.Println("============================================================")
	fmt.Printf("  Part3: 難易度設計テーブル (trials=%d)\n", trials)
	fmt.Println("  「1d10 + 属性ダイス1個」の組み合わせ別 成功率")
	fmt.Println("  ※ 目標値以上の達成値で成功")
	fmt.Println("============================================================")

	fmt.Print("目標値  ")
	for _, c := range DifficultyCombos {
		fmt.Printf("  %-12s", c.Name)
	}
	fmt.Println()
	fmt.Print("------  ")
	for range DifficultyCombos {
		fmt.Print("  ------------")
	}
	fmt.Println()

	rates := make([][]float64, TargetMax-TargetMin+1)
	for i := range rates {
		rates[i] = make([]float64, len(DifficultyCombos))
	}

	for tgt := TargetMin; tgt <= TargetMax; tgt++ {
		fmt.Printf("%6d  ", tgt)
		row := tgt - TargetMin
		for c, combo := range DifficultyCombos {
			rate := dice.SimulateSuccessRate(combo.Pool, trials, tgt, rng)
			rates[row][c] = rate
			fmt.Printf("  %11.1f%%", rate*100.0)
		}
		fmt.Println()
		fmt.Printf("PROGRESS3: %d / %d\n", tgt, TargetMax)
	}

	csvDir, err := dice.EnsureCSVDir(outDir)
	if err != nil {
		return err
	}
	path := filepath.Join(csvDir, "difficulty_table.csv")
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()

	w := csv.NewWriter(f)
	header := make([]string, 1+len(DifficultyCombos))
	header[0] = "target"
	for i, c := range DifficultyCombos {
		header[i+1] = c.Name
	}
	if err := w.Write(header); err != nil {
		return err
	}

	for tgt := TargetMin; tgt <= TargetMax; tgt++ {
		row := make([]string, len(header))
		row[0] = fmt.Sprintf("%d", tgt)
		for c := range DifficultyCombos {
			row[c+1] = fmt.Sprintf("%.4f", rates[tgt-TargetMin][c])
		}
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	fmt.Printf("\nCSV output: %s\n", path)
	return w.Error()
}
