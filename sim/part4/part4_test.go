package main

import (
	"math"
	"testing"
)

func TestPercentile(t *testing.T) {
	s := make([]int, 100)
	for i := range s {
		s[i] = i + 1
	}
	if got := percentile(s, 0.99); got != 99 {
		t.Fatalf("p99 got %d want 99", got)
	}
	if got := percentile(s, 0.50); got != 50 && got != 51 {
		t.Fatalf("p50 got %d", got)
	}
}

func TestDPCRatioOptimal(t *testing.T) {
	if math.Abs(dpcRatio(0, 0)-1.5) > 1e-9 {
		t.Fatalf("軽量軽行動: %v", dpcRatio(0, 0))
	}
	if math.Abs(dpcRatio(1, 1)-1.5) > 1e-9 {
		t.Fatalf("中量中行動: %v", dpcRatio(1, 1))
	}
	want := 11.0 / 7.0
	if math.Abs(dpcRatio(2, 3)-want) > 1e-9 {
		t.Fatalf("重量特行動: %v", dpcRatio(2, 3))
	}
}

func TestPrefixMax(t *testing.T) {
	got := prefixMax([]int{10, 8, 20, 15})
	want := []int{10, 10, 20, 20}
	if len(got) != len(want) {
		t.Fatalf("len %d", len(got))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("i=%d got %d want %d", i, got[i], want[i])
		}
	}
}

func TestWeaponHit(t *testing.T) {
	if got := weaponHit(17, 7, 6); got != 12 {
		t.Fatalf("等級7: %d", got)
	}
	if got := weaponHit(17, 10, 6); got != 6 {
		t.Fatalf("等級10: %d", got)
	}
	if got := weaponHit(17, 18, 6); got != 0 {
		t.Fatalf("錬価0: %d", got)
	}
}

func TestHitsToKill(t *testing.T) {
	if got := hitsToKill(20, 12); got != 2 {
		t.Fatalf("20/12: %d", got)
	}
	if got := hitsToKill(25, 12); got != 3 {
		t.Fatalf("25/12: %d", got)
	}
	if got := hitsToKill(25, 17); got != 2 {
		t.Fatalf("25/17: %d", got)
	}
	if got := hitsToKill(25, 25); got != 1 {
		t.Fatalf("25/25: %d", got)
	}
	if got := hitsToKill(25, 0); got != 0 {
		t.Fatalf("dmg0: %d", got)
	}
}

func TestCollectRecipeCounts(t *testing.T) {
	if got := len(collectRecipeCounts(0)); got != 1 {
		t.Fatalf("nAttr=0: %d", got)
	}
	if got := len(collectRecipeCounts(2)); got != 10 {
		t.Fatalf("nAttr=2: %d want 10", got)
	}
}

func TestFirstKAtLeast(t *testing.T) {
	vals := []float64{17, 20, 24, 26, 28}
	if got := firstKAtLeast(vals, 25); got != 4 {
		t.Fatalf("got %d want 4", got)
	}
	if got := firstKAtLeast(vals, 40); got != 0 {
		t.Fatalf("never: %d", got)
	}
}
