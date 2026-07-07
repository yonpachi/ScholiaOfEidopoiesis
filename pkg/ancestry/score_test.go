package ancestry_test

import (
	"math/rand"
	"testing"

	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/ancestry"
	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/dice"
)

func TestScoreMakinaReturnsScoreWithoutD10(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	pool := []int{4, 6, 8}
	score := ancestry.ScoreMakina(pool, rng)
	if score <= 0 {
		t.Fatalf("ScoreMakina score=%d, want positive baseline roll", score)
	}
}

func TestHomunculusConvergeHomogenizeAllOnes(t *testing.T) {
	rng := rand.New(rand.NewSource(0))
	raw := []dice.Die{
		{Sides: 10, Face: 1},
		{Sides: 4, Face: 1},
		{Sides: 6, Face: 1},
	}
	wantConverge := dice.DieValue(10, 5) + dice.DieValue(4, 2) + dice.DieValue(6, 3)
	score, opt := ancestry.ScoreHomunculus(raw, 3, rng)
	if score < wantConverge {
		t.Errorf("homunculus score=%d opt=%d, want at least converge floor %d", score, opt, wantConverge)
	}
	if opt != ancestry.HomoConverge {
		t.Errorf("homunculus opt=%d, want HomoConverge=%d on all-1 pool", opt, ancestry.HomoConverge)
	}
}
func TestHomunculusFixDisablesStickyPenalty(t *testing.T) {
	rng := rand.New(rand.NewSource(0))
	raw := []dice.Die{
		{Sides: 10, Face: 1},
		{Sides: 6, Face: 3},
	}
	var reacted [dice.MaxDice]dice.Die
	var used [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(raw, 2, reacted[:], used[:])
	n := 2
	dice.RunReactLoop(reacted[:], used[:], &n, &q, rng, 0)
	base := dice.ScoreBaseline(reacted[:], n)
	noSticky := dice.ScoreWithOpts(reacted[:], n, dice.ScoreOpts{NoSticky: true})
	if noSticky <= base {
		t.Errorf("NoSticky=%d should exceed sticky baseline=%d when face 1 present", noSticky, base)
	}
	score, opt := ancestry.ScoreHomunculus(raw, 2, rng)
	if score < noSticky {
		t.Errorf("homunculus score=%d opt=%d, want at least fix score %d", score, opt, noSticky)
	}
}
