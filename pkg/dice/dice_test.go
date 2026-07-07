package dice_test

import (
	"math/rand"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/dice"
)

func TestDieValue(t *testing.T) {
	cases := []struct {
		sides, face, want int
	}{
		{10, 1, -1},
		{10, 2, 2},
		{10, 5, 5},
		{20, 1, -1},
		{20, 2, -1},
		{20, 3, -1},
		{20, 4, 2},
		{20, 20, 10},
		{6, 1, -1},
		{6, 6, 6},
	}
	for _, c := range cases {
		if got := dice.DieValue(c.sides, c.face); got != c.want {
			t.Errorf("DieValue(%d,%d) = %d, want %d", c.sides, c.face, got, c.want)
		}
	}
}

func TestDieValueNoPenalty(t *testing.T) {
	cases := []struct {
		sides, face, want int
	}{
		{10, 1, 1},
		{20, 1, 0},
		{20, 2, 1},
		{20, 4, 2},
	}
	for _, c := range cases {
		if got := dice.DieValueNoPenalty(c.sides, c.face); got != c.want {
			t.Errorf("DieValueNoPenalty(%d,%d) = %d, want %d", c.sides, c.face, got, c.want)
		}
	}
}

func TestPart1D20NotMislabeled(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	pool := make([]int, 5)
	for i := range pool {
		pool[i] = 20
	}
	stats := dice.SimulatePool(pool, 10000, rng)
	avgPerDie := stats.Avg / 5.0
	if avgPerDie > 7.0 {
		t.Errorf("d20 avg/die = %.3f, expected ~5 (floor/2 + reactions), possible label/scoring bug", avgPerDie)
	}
}

func TestSimulatePoolDeterministic(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	pool := []int{10, 4}
	stats := dice.SimulatePool(pool, 5000, rng)
	if stats.Avg < 5 || stats.Avg > 15 {
		t.Errorf("unexpected avg %f for d10+d4 pool", stats.Avg)
	}
}

func TestBuildPoolIncludesD12(t *testing.T) {
	pool := make([]int, 3)
	counts := [5]int{0, 0, 0, 1, 1} // d10, d20
	n := dice.BuildPool(counts, true, pool)
	if n != 3 {
		t.Fatalf("BuildPool n = %d, want 3", n)
	}
	want := []int{10, 20, 12}
	for i, w := range want {
		if pool[i] != w {
			t.Errorf("pool[%d] = %d, want %d", i, pool[i], w)
		}
	}
}

func TestBuildRecipePool(t *testing.T) {
	pool := make([]int, 4)
	counts := [4]int{1, 0, 1, 1} // d4×1, d8×1, d20×1
	n := dice.BuildRecipePool(counts, pool)
	if n != 4 {
		t.Fatalf("BuildRecipePool n = %d, want 4", n)
	}
	want := []int{10, 4, 8, 20}
	for i, w := range want {
		if pool[i] != w {
			t.Errorf("pool[%d] = %d, want %d", i, pool[i], w)
		}
	}
}

func TestEffectD12TargetsReactedDie(t *testing.T) {
	rng := rand.New(rand.NewSource(0))
	var diceArr [dice.MaxDice]dice.Die
	diceArr[0] = dice.Die{Sides: 10, Face: 1}
	diceArr[1] = dice.Die{Sides: 12, Face: 12}
	var used [dice.MaxDice]int
	used[0] = 1 // d10 already reacted; d12 may still target it
	nDice := 2

	dice.ReactAll(diceArr[:], used[:], &nDice, rng)

	if diceArr[0].Face != 10 {
		t.Errorf("reacted d10 face = %d, want 10 after d12 ascend", diceArr[0].Face)
	}
	if dice.ScoreBaseline(diceArr[:], nDice) < 20 {
		t.Errorf("score after ascend = %d, expected at least 20", dice.ScoreBaseline(diceArr[:], nDice))
	}
}
