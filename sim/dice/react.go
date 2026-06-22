package dice

import "math/rand"

func applyReaction(dice []Die, nDice *int, used []int, q *queue, idx int, rng *rand.Rand) int {
	prevN := *nDice
	switch dice[idx].Sides {
	case 4:
		effectD4(dice, nDice, q, idx, rng)
	case 6:
		effectD6(dice, *nDice, q, idx, used)
	case 8:
		effectD8(dice, *nDice, q, idx, used)
	case 10:
		effectD10(dice, *nDice, q, idx, used)
	case 12:
		effectD12(dice, *nDice, q, idx, used)
	case 20:
		effectD20(dice, *nDice, q, idx, used, rng)
	}
	return prevN
}

// runReactLoop runs the reaction queue until empty. skipTriggerSides>0 skips enqueue on that Die size.
func runReactLoop(dice []Die, used []int, nDice *int, q *queue, rng *rand.Rand, skipTriggerSides int) {
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

// runReactLoopSteps runs at most maxSteps reactions; maxSteps<0 means unlimited. Returns steps executed.
func runReactLoopSteps(dice []Die, used []int, nDice *int, q *queue, rng *rand.Rand, maxSteps int) int {
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

func scoreBaseline(dice []Die, nDice int) int {
	total := 0
	for i := 0; i < nDice; i++ {
		total += DieValue(dice[i].Sides, dice[i].Face)
	}
	return total
}

func copyDiceState(src []Die, n int, dst []Die, usedDst []int) {
	copy(dst[:n], src[:n])
	for i := 0; i < n; i++ {
		usedDst[i] = 0
	}
}
