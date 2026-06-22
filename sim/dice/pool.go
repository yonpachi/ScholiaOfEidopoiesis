package dice

import "math/rand"

type Die struct {
	Sides int
	Face  int
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

func effectD4(dice []Die, nDice *int, q *queue, idx int, rng *rand.Rand) {
	if dice[idx].Face < 3 {
		return
	}
	dice[idx].Face = 4
	newFace := rng.Intn(4) + 1
	dice[*nDice] = Die{Sides: 4, Face: newFace}
	q.push(*nDice)
	*nDice++
}

func effectD6(dice []Die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].Face != 6 {
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
		n := dice[j].Sides
		oldF := dice[j].Face
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
	dice[bestTarget].Face = bestNewFace
	if triggers(dice[bestTarget].Sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD8(dice []Die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].Face != 8 {
		return
	}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].Sides
		if n%2 != 0 {
			continue
		}
		oldF := dice[j].Face
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
	dice[bestTarget].Face = bestNewFace
	if triggers(dice[bestTarget].Sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD10(dice []Die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].Face != 10 {
		return
	}
	bestGain := 0
	bestTarget := -1
	bestNewFace := 0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].Sides
		oldF := dice[j].Face
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
	dice[bestTarget].Face = bestNewFace
	if triggers(dice[bestTarget].Sides, bestNewFace) {
		q.push(bestTarget)
	}
}

func effectD12(dice []Die, nDice int, q *queue, idx int, used []int) {
	if dice[idx].Face != 12 {
		return
	}
	bestGain := 0
	bestTarget := -1

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].Sides
		oldF := dice[j].Face
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
	dice[bestTarget].Face = dice[bestTarget].Sides
	if triggers(dice[bestTarget].Sides, dice[bestTarget].Sides) {
		q.push(bestTarget)
	}
}

func effectD20(dice []Die, nDice int, q *queue, idx int, used []int, rng *rand.Rand) {
	if dice[idx].Face != 20 {
		return
	}
	bestTarget := -1
	bestExpectedGain := 0.0

	for j := 0; j < nDice; j++ {
		if j == idx || used[j] != 0 {
			continue
		}
		n := dice[j].Sides
		oldVal := DieValue(n, dice[j].Face)
		expectedGain := expectedDieValue(n) - float64(oldVal)
		if expectedGain > bestExpectedGain {
			bestExpectedGain = expectedGain
			bestTarget = j
		}
	}
	if bestTarget < 0 {
		return
	}
	n := dice[bestTarget].Sides
	newFace := rng.Intn(n) + 1
	dice[bestTarget].Face = newFace
	if triggers(n, newFace) {
		q.push(bestTarget)
	}
}

func enqueueInitialTriggers(dice []Die, nDice int, q *queue) {
	for i := 0; i < nDice; i++ {
		if triggers(dice[i].Sides, dice[i].Face) {
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
func SimulatePool(poolSides []int, trials int, rng *rand.Rand) PoolStats {
	totals := make([]int, trials)
	var dice [MaxDice]Die
	var used [MaxDice]int
	var q queue

	for t := 0; t < trials; t++ {
		totals[t] = simulateTrialTotal(poolSides, rng, &dice, &used, &q)
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

// SimulateSuccessRate returns the fraction of trials where total achievement >= target.
func SimulateSuccessRate(poolSides []int, trials, target int, rng *rand.Rand) float64 {
	var dice [MaxDice]Die
	var used [MaxDice]int
	var q queue
	success := 0
	for t := 0; t < trials; t++ {
		if simulateTrialTotal(poolSides, rng, &dice, &used, &q) >= target {
			success++
		}
	}
	return float64(success) / float64(trials)
}

func simulateTrialTotal(poolSides []int, rng *rand.Rand, dice *[MaxDice]Die, used *[MaxDice]int, q *queue) int {
	nDice := len(poolSides)
	for i := 0; i < nDice; i++ {
		dice[i] = Die{Sides: poolSides[i], Face: rng.Intn(poolSides[i]) + 1}
		used[i] = 0
	}
	runReactLoop(dice[:], used[:], &nDice, q, rng, 0)
	return scoreBaseline(dice[:], nDice)
}

func sortInts(a []int) {
	for i := 1; i < len(a); i++ {
		for j := i; j > 0 && a[j-1] > a[j]; j-- {
			a[j-1], a[j] = a[j], a[j-1]
		}
	}
}
