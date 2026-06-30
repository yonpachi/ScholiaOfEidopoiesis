package dice

const (
	MaxDice  = 256
	MaxQueue = 512
	MaxN     = 10
	Base     = 11
)

// DiceSides lists die sizes for part1 full pool enumeration (d12 appended last by BuildPool).
var DiceSides = [5]int{4, 6, 8, 10, 20}

// DiceNames column order for part1 marginal CSV.
var DiceNames = [6]string{"d4", "d6", "d8", "d10", "d20", "d12"}

// AttrSides lists recipe attribute die sizes for part2 (base d10 is separate).
var AttrSides = [4]int{4, 6, 8, 20}

const BaseD10 = 10

// DieValue maps a rolled face to achievement contribution (with penalty rules).
func DieValue(sides, face int) int {
	if face == 1 {
		return -1
	}
	if sides == 20 && face <= 3 {
		return -1
	}
	if sides == 20 {
		return face / 2
	}
	return face
}

// DieValueNoPenalty maps a face without sticky (-1) penalty.
func DieValueNoPenalty(sides, face int) int {
	if sides == 20 {
		return face / 2
	}
	return face
}

func cyclicAdjust(sides, face, delta int) int {
	idx := face - 1
	idx = ((idx+delta)%sides + sides) % sides
	return idx + 1
}

func invertFace(sides, face int) int {
	return sides + 1 - face
}

func halfTurnFace(sides, face int) int {
	return cyclicAdjust(sides, face, sides/2)
}

func triggers(sides, face int) bool {
	switch sides {
	case 4:
		return face >= 3
	case 6:
		return face == 6
	case 8:
		return face == 8
	case 10:
		return face == 10
	case 12:
		return face == 12
	case 20:
		return face == 20
	default:
		return false
	}
}

func expectedDieValue(sides int) float64 {
	sum := 0.0
	for f := 1; f <= sides; f++ {
		sum += float64(DieValue(sides, f))
	}
	return sum / float64(sides)
}
