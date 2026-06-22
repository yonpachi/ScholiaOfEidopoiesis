package dice

import "math/rand"

const NRaces = 6

// RaceNamesCSV matches monte_carlo.c CSV column headers.
var RaceNamesCSV = [NRaces]string{
	"Hume", "Makina", "Bestia", "Homunculus", "Relicia", "Umbra",
}

func ScoreHuman(diceRaw []Die, nRaw int, rng *rand.Rand) (int, bool) {
	var baseDice [MaxDice]Die
	var usedBase [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, baseDice[:], usedBase[:])
	nBase := nRaw
	runReactLoop(baseDice[:], usedBase[:], &nBase, &q, rng, 0)
	best := scoreBaseline(baseDice[:], nBase)
	used := false

	var t [MaxDice]Die
	var u [MaxDice]int
	for i := 0; i < nRaw; i++ {
		n := diceRaw[i].Sides
		oldF := diceRaw[i].Face
		newF := invertFace(n, oldF)
		gain := DieValue(n, newF) - DieValue(n, oldF)
		if gain <= 0 {
			continue
		}
		copyDiceState(diceRaw, nRaw, t[:], u[:])
		t[i].Face = newF
		u[i] = 1
		nn := nRaw
		runReactLoop(t[:], u[:], &nn, &q, rng, 0)
		s := scoreBaseline(t[:], nn) - nRaw
		if s > best {
			best = s
			used = true
		}
	}
	return best, used
}

func ScoreBeast(diceRaw []Die, nRaw int, rng *rand.Rand) (int, bool) {
	bestTarget := -1
	bestGain := 0.0
	for i := 0; i < nRaw; i++ {
		n := diceRaw[i].Sides
		oldFace := diceRaw[i].Face
		oldVal := DieValue(n, oldFace)
		expNew := 0.0
		for f := 1; f <= n; f++ {
			val := DieValue(n, f)
			if f < oldFace {
				val = -1
			}
			expNew += float64(val)
		}
		expNew /= float64(n)
		if g := expNew - float64(oldVal); g > bestGain {
			bestGain = g
			bestTarget = i
		}
	}

	var tmp [MaxDice]Die
	var used [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, tmp[:], used[:])
	abilityUsed := bestTarget >= 0
	if abilityUsed {
		oldFace := tmp[bestTarget].Face
		newFace := rng.Intn(tmp[bestTarget].Sides) + 1
		if newFace < oldFace {
			newFace = 1
		}
		tmp[bestTarget].Face = newFace
	}
	n := nRaw
	runReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	return scoreBaseline(tmp[:], n), abilityUsed
}

func ScoreHomunculus(diceRaw []Die, nRaw int, rng *rand.Rand) (int, int) {
	var reacted [MaxDice]Die
	var usedR [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, reacted[:], usedR[:])
	nR := nRaw
	runReactLoop(reacted[:], usedR[:], &nR, &q, rng, 0)
	base := scoreBaseline(reacted[:], nR)
	bestScore := base
	bestOption := -1

	{
		s := 0
		for i := 0; i < nR; i++ {
			s += DieValueNoPenalty(reacted[i].Sides, reacted[i].Face)
		}
		if s > bestScore {
			bestScore = s
			bestOption = 0
		}
	}

	{
		reactedCount := 0
		for i := 0; i < nR; i++ {
			reactedCount += usedR[i]
		}
		s := base + reactedCount/2
		if s > bestScore {
			bestScore = s
			bestOption = 1
		}
	}

	if nRaw >= 2 {
		var tmp0 [MaxDice]Die
		var used0 [MaxDice]int
		copyDiceState(diceRaw, nRaw, tmp0[:], used0[:])
		nn0 := nRaw
		totalSteps := runReactLoopSteps(tmp0[:], used0[:], &nn0, &q, rng, -1)

		for k := 0; k <= totalSteps; k++ {
			var tmp [MaxDice]Die
			var used [MaxDice]int
			copyDiceState(diceRaw, nRaw, tmp[:], used[:])
			nn := nRaw
			runReactLoopSteps(tmp[:], used[:], &nn, &q, rng, k)
			cost := nn

			drop := 0
			bestVal := DieValue(tmp[0].Sides, tmp[0].Face)
			for i := 1; i < nn; i++ {
				v := DieValue(tmp[i].Sides, tmp[i].Face)
				if v > bestVal {
					bestVal = v
					drop = i
				}
			}

			var t2 [MaxDice]Die
			var u2 [MaxDice]int
			nn2 := 0
			for i := 0; i < nn; i++ {
				if i == drop {
					continue
				}
				t2[nn2] = tmp[i]
				t2[nn2].Face = cyclicAdjust(t2[nn2].Sides, t2[nn2].Face, 1)
				u2[nn2] = used[i]
				nn2++
			}
			runReactLoop(t2[:], u2[:], &nn2, &q, rng, 0)
			s := scoreBaseline(t2[:], nn2) - cost
			if s > bestScore {
				bestScore = s
				bestOption = 2
			}
		}
	} else {
		var tmp [MaxDice]Die
		var used [MaxDice]int
		copyDiceState(diceRaw, nRaw, tmp[:], used[:])
		tmp[0].Face = cyclicAdjust(tmp[0].Sides, tmp[0].Face, 1)
		nn := nRaw
		runReactLoop(tmp[:], used[:], &nn, &q, rng, 0)
		s := scoreBaseline(tmp[:], nn) - nn
		if s > bestScore {
			bestScore = s
			bestOption = 2
		}
	}

	return bestScore, bestOption
}

func ScoreRelicia(diceRaw []Die, nRaw int, rng *rand.Rand) (int, bool) {
	bestTarget := -1
	bestExpGain := 0.0
	for i := 0; i < nRaw; i++ {
		n := diceRaw[i].Sides
		oldFace := diceRaw[i].Face
		oldVal := DieValue(n, oldFace)
		expNew := 0.0
		for f := 1; f <= n; f++ {
			val := DieValue(n, f)
			if f <= oldFace {
				val = oldVal
			}
			expNew += float64(val)
		}
		expNew /= float64(n)
		if g := expNew - float64(oldVal); g > bestExpGain {
			bestExpGain = g
			bestTarget = i
		}
	}

	var tmp [MaxDice]Die
	var used [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, tmp[:], used[:])
	abilityUsed := bestTarget >= 0
	if abilityUsed {
		oldFace := tmp[bestTarget].Face
		newFace := rng.Intn(tmp[bestTarget].Sides) + 1
		if newFace <= oldFace {
			newFace = oldFace
		}
		tmp[bestTarget].Face = newFace
		used[bestTarget] = 1
	}
	n := nRaw
	runReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	return scoreBaseline(tmp[:], n) + 1, abilityUsed
}

func ScoreUmbra(diceRaw []Die, nRaw int, rng *rand.Rand) (int, bool) {
	var tmp [MaxDice]Die
	var used [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, tmp[:], used[:])
	n := nRaw
	runReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	baseScore := scoreBaseline(tmp[:], n)

	bestTarget := -1
	bestGain := 0.0
	for i := 0; i < n; i++ {
		if used[i] == 0 {
			continue
		}
		if !triggers(tmp[i].Sides, tmp[i].Face) {
			continue
		}
		var t2 [MaxDice]Die
		var u2 [MaxDice]int
		copy(t2[:n], tmp[:n])
		copy(u2[:n], used[:n])
		u2[i] = 0
		n2 := n
		runReactLoop(t2[:], u2[:], &n2, &q, rng, 0)
		if g := float64(scoreBaseline(t2[:], n2) - baseScore); g > bestGain {
			bestGain = g
			bestTarget = i
		}
	}
	if bestTarget < 0 {
		return baseScore, false
	}
	used[bestTarget] = 0
	runReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	return scoreBaseline(tmp[:], n), true
}

func ScoreMakina(pool []int, rng *rand.Rand) int {
	replaced := make([]int, len(pool))
	copy(replaced, pool)
	for i := range replaced {
		if replaced[i] == 10 {
			replaced[i] = 12
			break
		}
	}

	var dice [MaxDice]Die
	var used [MaxDice]int
	var q queue
	n := len(replaced)
	for i := 0; i < n; i++ {
		dice[i] = Die{Sides: replaced[i], Face: rng.Intn(replaced[i]) + 1}
		used[i] = 0
	}
	runReactLoop(dice[:], used[:], &n, &q, rng, 0)
	total := 0
	for i := 0; i < n; i++ {
		total += DieValueNoPenalty(dice[i].Sides, dice[i].Face)
	}
	return total
}

func BaselineFromRaw(diceRaw []Die, nRaw int, rng *rand.Rand) int {
	var baseDice [MaxDice]Die
	var usedBase [MaxDice]int
	var q queue
	copyDiceState(diceRaw, nRaw, baseDice[:], usedBase[:])
	nBase := nRaw
	runReactLoop(baseDice[:], usedBase[:], &nBase, &q, rng, 0)
	return scoreBaseline(baseDice[:], nBase)
}

// ScoreByRace applies the given race ability (0..NRaces-1) and returns total achievement.
func ScoreByRace(race int, pool []int, diceRaw []Die, nPool int, rng *rand.Rand) int {
	switch race {
	case 0:
		s, _ := ScoreHuman(diceRaw, nPool, rng)
		return s
	case 1:
		return ScoreMakina(pool, rng)
	case 2:
		s, _ := ScoreBeast(diceRaw, nPool, rng)
		return s
	case 3:
		s, _ := ScoreHomunculus(diceRaw, nPool, rng)
		return s
	case 4:
		s, _ := ScoreRelicia(diceRaw, nPool, rng)
		return s
	case 5:
		s, _ := ScoreUmbra(diceRaw, nPool, rng)
		return s
	default:
		return 0
	}
}
