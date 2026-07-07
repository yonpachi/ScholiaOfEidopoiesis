package dice

import "math/rand"

// ScoreOpts controls achievement scoring variants.
type ScoreOpts struct {
	NoSticky    bool // 澱み無効: 換算後1以下を−1にしない
	PerDieMinus int  // 各ダイス換算から減算（将来拡張用）
}

// ScoreWithOpts sums achievement values with optional modifiers.
func ScoreWithOpts(dice []Die, nDice int, opts ScoreOpts) int {
	total := 0
	for i := 0; i < nDice; i++ {
		sides := dice[i].Sides
		face := dice[i].Face
		var v int
		if opts.NoSticky {
			v = DieValueNoPenalty(sides, face)
		} else {
			v = DieValue(sides, face)
		}
		if opts.PerDieMinus > 0 {
			v -= opts.PerDieMinus
		}
		total += v
	}
	return total
}

// BaselineFromRaw runs greedy reactions on a fixed roll without race abilities.
func BaselineFromRaw(diceRaw []Die, nRaw int, rng *rand.Rand) int {
	var baseDice [MaxDice]Die
	var usedBase [MaxDice]int
	var q Queue
	CopyDiceState(diceRaw, nRaw, baseDice[:], usedBase[:])
	nBase := nRaw
	RunReactLoop(baseDice[:], usedBase[:], &nBase, &q, rng, 0)
	return ScoreBaseline(baseDice[:], nBase)
}

// WrapFace maps face into 1..sides using cyclic wrap (for crossover overflow).
func WrapFace(sides, face int) int {
	if sides < 1 {
		return face
	}
	idx := face - 1
	idx = ((idx % sides) + sides) % sides
	return idx + 1
}

// SwapCrossoverFaces swaps faces of two dice; out-of-range results wrap cyclically.
func SwapCrossoverFaces(a, b *Die) {
	fa, fb := a.Face, b.Face
	a.Face = WrapFace(a.Sides, fb)
	b.Face = WrapFace(b.Sides, fa)
}

// InvertFace returns the inverted face (N+1-face).
func InvertFace(sides, face int) int {
	return invertFace(sides, face)
}

// CyclicAdjust moves face by delta on a cyclic die.
func CyclicAdjust(sides, face, delta int) int {
	return cyclicAdjust(sides, face, delta)
}

// Triggers reports whether face meets the reaction threshold for sides.
func Triggers(sides, face int) bool {
	return triggers(sides, face)
}
