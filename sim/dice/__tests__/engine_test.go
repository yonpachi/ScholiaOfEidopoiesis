package dice_test

import (
	"math/rand"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

func TestDieValue(t *testing.T) {
	cases := []struct {
		sides, face, want int
	}{
		{10, 1, -1},
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

func TestScoreHumanUsesCost(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	raw := []dice.Die{{Sides: 10, Face: 1}}
	n := 1
	base := dice.BaselineFromRaw(raw, n, rng)
	score, used := dice.ScoreHuman(raw, n, rng)
	if !used {
		t.Fatal("expected human to invert d10 face 1")
	}
	if score <= base {
		t.Errorf("human score %d should exceed base %d after invert+react", score, base)
	}
}
