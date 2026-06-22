package dice

func CacheIdx(counts [5]int, d12 int) int {
	idx := counts[0]
	for i := 1; i < 5; i++ {
		idx = idx*Base + counts[i]
	}
	return idx + d12*(Base*Base*Base*Base*Base)
}

func BuildPool(counts [5]int, hasD12 bool, pool []int) int {
	np := 0
	for t := 0; t < 5; t++ {
		for k := 0; k < counts[t]; k++ {
			pool[np] = DiceSides[t]
			np++
		}
	}
	if hasD12 {
		pool[np] = 12
		np++
	}
	return np
}
