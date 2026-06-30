package dice

import "math/rand"

// ReactAll applies greedy reactions until no reactive dice remain.
func ReactAll(dice []Die, used []int, nDice *int, rng *rand.Rand) {
	var q Queue
	RunReactLoop(dice, used, nDice, &q, rng, 0)
}

func applyReaction(dice []Die, nDice *int, used []int, q *Queue, idx int, rng *rand.Rand) int {
	prevN := *nDice
	switch dice[idx].Sides {
	case 4:
		effectD4(dice, nDice, q, idx, rng)
	case 6:
		effectD6(dice, *nDice, q, idx)
	case 8:
		effectD8(dice, *nDice, q, idx)
	case 10:
		effectD10(dice, *nDice, q, idx)
	case 12:
		effectD12(dice, *nDice, q, idx)
	case 20:
		effectD20(dice, *nDice, q, idx, rng)
	}
	return prevN
}

// RunReactLoop runs the reaction queue until empty. skipTriggerSides>0 skips enqueue on that Die size.
func RunReactLoop(dice []Die, used []int, nDice *int, q *Queue, rng *rand.Rand, skipTriggerSides int) {
	q.clear()
	for i := 0; i < *nDice; i++ {
		if skipTriggerSides != 0 && dice[i].Sides == skipTriggerSides {
			continue
		}
		if triggers(dice[i].Sides, dice[i].Face) {
			q.push(i)
		}
	}
	for !q.empty() {
		idx := q.pop()
		if used[idx] != 0 {
			continue
		}
		if !triggers(dice[idx].Sides, dice[idx].Face) {
			continue
		}
		used[idx] = 1
		prevN := applyReaction(dice, nDice, used, q, idx, rng)
		for i := prevN; i < *nDice; i++ {
			used[i] = 0
		}
	}
}

// RunReactLoopSteps runs at most maxSteps reactions; maxSteps<0 means unlimited. Returns steps executed.
func RunReactLoopSteps(dice []Die, used []int, nDice *int, q *Queue, rng *rand.Rand, maxSteps int) int {
	q.clear()
	for i := 0; i < *nDice; i++ {
		if triggers(dice[i].Sides, dice[i].Face) {
			q.push(i)
		}
	}
	steps := 0
	for !q.empty() {
		if maxSteps >= 0 && steps >= maxSteps {
			break
		}
		idx := q.pop()
		if used[idx] != 0 {
			continue
		}
		if !triggers(dice[idx].Sides, dice[idx].Face) {
			continue
		}
		used[idx] = 1
		steps++
		prevN := applyReaction(dice, nDice, used, q, idx, rng)
		for i := prevN; i < *nDice; i++ {
			used[i] = 0
		}
	}
	return steps
}

// ScoreBaseline sums achievement values for all dice in the pool.
func ScoreBaseline(dice []Die, nDice int) int {
	total := 0
	for i := 0; i < nDice; i++ {
		total += DieValue(dice[i].Sides, dice[i].Face)
	}
	return total
}

// CopyDiceState copies dice faces and resets used flags.
func CopyDiceState(src []Die, n int, dst []Die, usedDst []int) {
	copy(dst[:n], src[:n])
	for i := 0; i < n; i++ {
		usedDst[i] = 0
	}
}
