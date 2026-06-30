package dice

// CacheIdx maps a 5-type count vector plus optional d12 to a flat cache index.
func CacheIdx(counts [5]int, d12 int) int {
	idx := counts[0]
	for i := 1; i < 5; i++ {
		idx = idx*Base + counts[i]
	}
	return idx + d12*(Base*Base*Base*Base*Base)
}

// CacheSize returns the number of slots for the pass-1 cache (d12 present or not).
func CacheSize() int {
	return Base * Base * Base * Base * Base * 2
}
