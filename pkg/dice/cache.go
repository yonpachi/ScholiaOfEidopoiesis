package dice

// PoolCacheIdx maps a full pool count vector (d4..d20) plus optional d12 to a cache index (part1).
func PoolCacheIdx(counts [5]int, d12 int) int {
	idx := counts[0]
	for i := 1; i < 5; i++ {
		idx = idx*Base + counts[i]
	}
	return idx + d12*(Base*Base*Base*Base*Base)
}

// PoolCacheSize returns pass-1 cache slots (Base^5 × 2 for optional d12).
func PoolCacheSize() int {
	return Base * Base * Base * Base * Base * 2
}
