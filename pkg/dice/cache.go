package dice

// CacheIdx maps a 6-type dice count vector to a flat cache index (Base=11 per dimension).
func CacheIdx(counts [6]int) int {
	idx := counts[0]
	for i := 1; i < 6; i++ {
		idx = idx*Base + counts[i]
	}
	return idx
}

// CacheSize returns the number of slots for the full count cache (Base^6).
func CacheSize() int {
	n := 1
	for i := 0; i < 6; i++ {
		n *= Base
	}
	return n
}
