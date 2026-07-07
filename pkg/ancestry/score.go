package ancestry

import (
	"math/rand"

	"github.com/yonpachi/ScholiaOfEidopoiesis/pkg/dice"
)

// ScoreHuman applies 翻転 (activation cost: subtract nRaw from score).
func ScoreHuman(diceRaw []dice.Die, nRaw int, rng *rand.Rand) (int, bool) {
	var baseDice [dice.MaxDice]dice.Die
	var usedBase [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(diceRaw, nRaw, baseDice[:], usedBase[:])
	nBase := nRaw
	dice.RunReactLoop(baseDice[:], usedBase[:], &nBase, &q, rng, 0)
	best := dice.ScoreBaseline(baseDice[:], nBase)
	used := false

	var t [dice.MaxDice]dice.Die
	var u [dice.MaxDice]int
	for i := 0; i < nRaw; i++ {
		n := diceRaw[i].Sides
		oldF := diceRaw[i].Face
		newF := dice.InvertFace(n, oldF)
		if dice.DieValue(n, newF)-dice.DieValue(n, oldF) <= 0 {
			continue
		}
		dice.CopyDiceState(diceRaw, nRaw, t[:], u[:])
		t[i].Face = newF
		u[i] = 1
		nn := nRaw
		dice.RunReactLoop(t[:], u[:], &nn, &q, rng, 0)
		s := dice.ScoreBaseline(t[:], nn) - nRaw
		if s > best {
			best = s
			used = true
		}
	}
	return best, used
}

// ScoreBeast applies 転機.
func ScoreBeast(diceRaw []dice.Die, nRaw int, rng *rand.Rand) (int, bool) {
	bestTarget := -1
	bestGain := 0.0
	for i := 0; i < nRaw; i++ {
		n := diceRaw[i].Sides
		oldFace := diceRaw[i].Face
		oldVal := dice.DieValue(n, oldFace)
		expNew := 0.0
		for f := 1; f <= n; f++ {
			val := dice.DieValue(n, f)
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

	var tmp [dice.MaxDice]dice.Die
	var used [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(diceRaw, nRaw, tmp[:], used[:])
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
	dice.RunReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	return dice.ScoreBaseline(tmp[:], n), abilityUsed
}

// ScoreMakina applies 素読 (base d10 → d12, no sticky).
func ScoreMakina(pool []int, rng *rand.Rand) int {
	replaced := make([]int, len(pool))
	copy(replaced, pool)
	for i := range replaced {
		if replaced[i] == 10 {
			replaced[i] = 12
			break
		}
	}

	var diceArr [dice.MaxDice]dice.Die
	var used [dice.MaxDice]int
	var q dice.Queue
	n := len(replaced)
	for i := 0; i < n; i++ {
		diceArr[i] = dice.Die{Sides: replaced[i], Face: rng.Intn(replaced[i]) + 1}
		used[i] = 0
	}
	dice.RunReactLoop(diceArr[:], used[:], &n, &q, rng, 0)
	return dice.ScoreWithOpts(diceArr[:], n, dice.ScoreOpts{NoSticky: true})
}

// HomunculusOption indexes 進化 choices: 0=修正, 1=発現, 2=収束.
const (
	HomoFix = iota
	HomoManifest
	HomoConverge
)

// ScoreHomunculus picks the best 進化 option for the trial.
func ScoreHomunculus(diceRaw []dice.Die, nRaw int, rng *rand.Rand) (int, int) {
	var reacted [dice.MaxDice]dice.Die
	var usedR [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(diceRaw, nRaw, reacted[:], usedR[:])
	nR := nRaw
	dice.RunReactLoop(reacted[:], usedR[:], &nR, &q, rng, 0)
	base := dice.ScoreBaseline(reacted[:], nR)
	bestScore := base
	bestOption := -1

	{
		s := dice.ScoreWithOpts(reacted[:], nR, dice.ScoreOpts{NoSticky: true})
		if s > bestScore {
			bestScore = s
			bestOption = HomoFix
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
			bestOption = HomoManifest
		}
	}

	{
		bestConverge, ok := scoreHomunculusConverge(diceRaw, nRaw, rng)
		if ok && bestConverge > bestScore {
			bestScore = bestConverge
			bestOption = HomoConverge
		}
	}

	return bestScore, bestOption
}

// scoreHomunculusConverge applies 進化・収束: all faces to ⌊s/2⌋, skip reaction.
func scoreHomunculusConverge(diceRaw []dice.Die, nRaw int, _ *rand.Rand) (int, bool) {
	var tmp [dice.MaxDice]dice.Die
	copy(tmp[:nRaw], diceRaw[:nRaw])
	for i := 0; i < nRaw; i++ {
		tmp[i].Face = tmp[i].Sides / 2
	}
	return dice.ScoreBaseline(tmp[:], nRaw), true
}

// ScoreRelicia applies 手馴: before reaction, reroll all dice (activation cost: subtract nRaw from score).
func ScoreRelicia(diceRaw []dice.Die, nRaw int, rng *rand.Rand) (int, bool) {
	best := dice.BaselineFromRaw(diceRaw, nRaw, rng)

	var tmp [dice.MaxDice]dice.Die
	var used [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(diceRaw, nRaw, tmp[:], used[:])
	for i := 0; i < nRaw; i++ {
		tmp[i].Face = rng.Intn(tmp[i].Sides) + 1
	}
	n := nRaw
	dice.RunReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	if s := dice.ScoreBaseline(tmp[:], n) - nRaw; s > best {
		return s, true
	}
	return best, false
}

// ScoreUmbra applies 越境: rewind one reacted die, or +1 achievement when none reacted.
func ScoreUmbra(diceRaw []dice.Die, nRaw int, rng *rand.Rand) (int, bool) {
	var tmp [dice.MaxDice]dice.Die
	var used [dice.MaxDice]int
	var q dice.Queue
	dice.CopyDiceState(diceRaw, nRaw, tmp[:], used[:])
	n := nRaw
	dice.RunReactLoop(tmp[:], used[:], &n, &q, rng, 0)

	bestScore := dice.ScoreBaseline(tmp[:], n)

	reactedCount := 0
	for i := 0; i < n; i++ {
		reactedCount += used[i]
	}
	if reactedCount == 0 {
		return bestScore + 1, true
	}

	bestTarget := -1
	for i := 0; i < n; i++ {
		if used[i] == 0 {
			continue
		}
		var trial [dice.MaxDice]dice.Die
		var trialUsed [dice.MaxDice]int
		copy(trial[:n], tmp[:n])
		copy(trialUsed[:n], used[:n])
		trialUsed[i] = 0
		nTrial := n
		dice.RunReactLoop(trial[:], trialUsed[:], &nTrial, &q, rng, 0)
		if s := dice.ScoreBaseline(trial[:], nTrial); s > bestScore {
			bestScore = s
			bestTarget = i
		}
	}
	if bestTarget < 0 {
		return dice.ScoreBaseline(tmp[:], n), false
	}
	used[bestTarget] = 0
	dice.RunReactLoop(tmp[:], used[:], &n, &q, rng, 0)
	return dice.ScoreBaseline(tmp[:], n), true
}

// ScoreByRace applies race r (Hume and Relicia subtract nPool from score when ability is used).
func ScoreByRace(race int, pool []int, diceRaw []dice.Die, nPool int, rng *rand.Rand) (int, bool) {
	switch race {
	case 0:
		return ScoreHuman(diceRaw, nPool, rng)
	case 1:
		return ScoreMakina(pool, rng), true
	case 2:
		return ScoreBeast(diceRaw, nPool, rng)
	case 3:
		s, opt := ScoreHomunculus(diceRaw, nPool, rng)
		return s, opt >= 0
	case 4:
		return ScoreRelicia(diceRaw, nPool, rng)
	case 5:
		return ScoreUmbra(diceRaw, nPool, rng)
	default:
		return 0, false
	}
}

// HomunculusOptionForTrial returns which 進化 option was chosen (-1 if none).
func HomunculusOptionForTrial(diceRaw []dice.Die, nPool int, rng *rand.Rand) int {
	_, opt := ScoreHomunculus(diceRaw, nPool, rng)
	return opt
}
