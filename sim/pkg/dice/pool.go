package dice

import "math/rand"

type die struct {
	sides int
	face  int
}

type queue struct {
	buf  [MaxQueue]int
	head int
	tail int
	size int
}

func (q *queue) clear() {
	q.head, q.tail, q.size = 0, 0, 0
}

func (q *queue) empty() bool {
	return q.size == 0
}

func (q *queue) push(v int) {
	q.buf[q.tail] = v
	q.tail = (q.tail + 1) % MaxQueue
	q.size++
}

func (q *queue) pop() int {
	v := q.buf[q.head]
	q.head = (q.head + 1) % MaxQueue
	q.size--
	return v
}

func effectD4(dice []die, nDice *int, q *queue, idx int, rng *rand.Rand) {
	if dice[idx].face < 3 {
		return
	}
	dice[idx].face = 4
	newFace := rng.Intn(4) + 1
	dice[*nDice] = die{sides: 4, face: newFace}
	q.push(*nDice)
	*nDice++
}

func effectD6(dice []die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].face != 6 {
		return
	}
	deltas := [4]int{-2, -1, 1, 2}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		oldF := dice[j].face
		for _, delta := range deltas {
			newF := cyclicAdjust(n, oldF, delta)
			gain := DieValue(n, newF) - DieValue(n, oldF)
			if gain > bestGain {
				bestGain = gain
				bestTarget = j
				bestNewFace = newF
			}
		}
	}
	if bestTarget < 0 {
		return
	}
	dice[bestTarget].face = bestNewFace
	if triggers(dice[bestTarget].sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD8Invert(dice []die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].face != 8 {
		return
	}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		oldF := dice[j].face
		newF := invertFace(n, oldF)
		gain := DieValue(n, newF) - DieValue(n, oldF)
		if gain > bestGain {
			bestGain = gain
			bestTarget = j
			bestNewFace = newF
		}
	}
	if bestTarget < 0 {
		return
	}
	dice[bestTarget].face = bestNewFace
	if triggers(dice[bestTarget].sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD8HalfTurn(dice []die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].face != 8 {
		return
	}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		if n%2 != 0 {
			continue
		}
		oldF := dice[j].face
		newF := halfTurnFace(n, oldF)
		gain := DieValue(n, newF) - DieValue(n, oldF)
		if gain > bestGain {
			bestGain = gain
			bestTarget = j
			bestNewFace = newF
		}
	}
	if bestTarget < 0 {
		return
	}
	dice[bestTarget].face = bestNewFace
	if triggers(dice[bestTarget].sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD10(dice []die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].face != 10 {
		return
	}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		oldF := dice[j].face
		newF := invertFace(n, oldF)
		gain := DieValue(n, newF) - DieValue(n, oldF)
		if gain > bestGain {
			bestGain = gain
			bestTarget = j
			bestNewFace = newF
		}
	}
	if bestTarget < 0 {
		return
	}
	dice[bestTarget].face = bestNewFace
	if triggers(dice[bestTarget].sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD12(dice []die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].face != 12 {
		return
	}
	bestGain := 0
	bestTarget := -1

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		oldF := dice[j].face
		newF := n
		gain := DieValue(n, newF) - DieValue(n, oldF)
		if gain > bestGain {
			bestGain = gain
			bestTarget = j
		}
	}
	if bestTarget < 0 {
		return
	}
	dice[bestTarget].face = dice[bestTarget].sides
	if triggers(dice[bestTarget].sides, dice[bestTarget].sides) {
		q.push(bestTarget)
	}
}

func effectD20(dice []die, nDice int, q *queue, idx int, used []int, rng *rand.Rand) {
	if dice[idx].face != 20 {
		return
	}
	bestTarget := -1
	bestExpectedGain := 0.0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].sides
		oldVal := DieValue(n, dice[j].face)
		expectedGain := expectedDieValue(n) - float64(oldVal)
		if expectedGain > bestExpectedGain {
			bestExpectedGain = expectedGain
			bestTarget = j
		}
	}
	if bestTarget < 0 {
		return
	}
	n := dice[bestTarget].sides
	newFace := rng.Intn(n) + 1
	dice[bestTarget].face = newFace
	if triggers(n, newFace) {
		q.push(bestTarget)
	}
}

func enqueueInitialTriggers(dice []die, nDice int, q *queue) {
	for i := 0; i < nDice; i++ {
		if triggers(dice[i].sides, dice[i].face) {
			q.push(i)
		}
	}
}

// PoolStats holds simulation output statistics.
type PoolStats struct {
	Avg float64
	P50 int
	P90 int
	P99 int
}

// SimulatePool runs Monte Carlo trials for a dice pool.
func SimulatePool(poolSides []int, trials int, wind WindMode, rng *rand.Rand) PoolStats {
	totals := make([]int, trials)
	var dice [MaxDice]die
	var used [MaxDice]int
	var q queue

	for t := 0; t < trials; t++ {
		nDice := len(poolSides)
		for i := 0; i < nDice; i++ {
			dice[i] = die{sides: poolSides[i], face: rng.Intn(poolSides[i]) + 1}
			used[i] = 0
		}

		q.clear()
		enqueueInitialTriggers(dice[:], nDice, &q)

		for !q.empty() {
			idx := q.pop()
			if used[idx] != 0 {
				continue
			}
			if !triggers(dice[idx].sides, dice[idx].face) {
				continue
			}
			used[idx] = 1
			prevN := nDice
			switch dice[idx].sides {
			case 4:
				effectD4(dice[:], &nDice, &q, idx, rng)
			case 6:
				effectD6(dice[:], nDice, &q, idx, used[:])
			case 8:
				if wind == WindInvert {
					effectD8Invert(dice[:], nDice, &q, idx, used[:])
				} else {
					effectD8HalfTurn(dice[:], nDice, &q, idx, used[:])
				}
			case 10:
				effectD10(dice[:], nDice, &q, idx, used[:])
			case 12:
				effectD12(dice[:], nDice, &q, idx, used[:])
			case 20:
				effectD20(dice[:], nDice, &q, idx, used[:], rng)
			}
			for i := prevN; i < nDice; i++ {
				used[i] = 0
			}
		}

		total := 0
		for i := 0; i < nDice; i++ {
			total += DieValue(dice[i].sides, dice[i].face)
		}
		totals[t] = total
	}

	sortInts(totals)
	sum := 0.0
	for _, v := range totals {
		sum += float64(v)
	}
	return PoolStats{
		Avg: sum / float64(trials),
		P50: totals[int(0.50*float64(trials-1))],
		P90: totals[int(0.90*float64(trials-1))],
		P99: totals[int(0.99*float64(trials-1))],
	}
}

func sortInts(a []int) {
	for i := 1; i < len(a); i++ {
		for j := i; j > 0 && a[j-1] > a[j]; j-- {
			a[j-1], a[j] = a[j], a[j-1]
		}
	}
}
