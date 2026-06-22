package dice

import (
	"encoding/csv"
	"fmt"
	"math"
	"math/rand"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"testing"
)

func TestDieValue(t *testing.T) {
	cases := []struct {
		sides, face, want int
	}{
		{10, 1, -1},
		{10, 5, 5},
		{20, 1, -1},
		{20, 3, -1},
		{20, 4, 2},
		{20, 20, 10},
		{6, 6, 6},
	}
	for _, c := range cases {
		if got := DieValue(c.sides, c.face); got != c.want {
			t.Errorf("DieValue(%d,%d) = %d, want %d", c.sides, c.face, got, c.want)
		}
	}
}

func TestSimulatePoolDeterministic(t *testing.T) {
	rng := rand.New(rand.NewSource(42))
	pool := []int{10, 4}
	stats := SimulatePool(pool, 5000, WindHalfTurn, rng)
	if stats.Avg < 5 || stats.Avg > 15 {
		t.Errorf("unexpected avg %f for d10+d4 pool", stats.Avg)
	}
}

func TestMarginalEnumerationProducesCSV(t *testing.T) {
	outDir := t.TempDir()
	rng := rand.New(rand.NewSource(42))
	if err := RunFullEnumeration(500, WindHalfTurn, outDir, rng); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(outDir, "marginal_by_n.csv")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("missing csv: %v", err)
	}
	data, has, err := readMarginalCSV(path)
	if err != nil {
		t.Fatal(err)
	}
	if !has[1][0] {
		t.Error("expected data for n_others=1 d4")
	}
	_ = data
}

func TestMarginalCSVAgainstC(t *testing.T) {
	if os.Getenv("RUN_C_COMPARE") == "" {
		t.Skip("set RUN_C_COMPARE=1 to compare with monte_carlo.exe")
	}

	root := filepath.Join("..", "..", "..")
	exe := filepath.Join(root, "monte_carlo.exe")
	if _, err := os.Stat(exe); err != nil {
		t.Skip("monte_carlo.exe not found; build C version first")
	}

	goOut := t.TempDir()
	cOut := t.TempDir()
	seed := "42"
	trials := 10000
	rng := rand.New(rand.NewSource(42))

	if err := RunFullEnumeration(trials, WindHalfTurn, goOut, rng); err != nil {
		t.Fatal(err)
	}

	cmd := exec.Command(exe, cOut, seed)
	cmd.Dir = root
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("monte_carlo.exe: %v\n%s", err, out)
	}

	goCSV := filepath.Join(goOut, "marginal_by_n.csv")
	cCSV := filepath.Join(cOut, "marginal_by_n.csv")
	if err := compareMarginalCSV(goCSV, cCSV, 5e-2); err != nil {
		t.Fatal(err)
	}
}

func compareMarginalCSV(a, b string, tol float64) error {
	ra, ha, err := readMarginalCSV(a)
	if err != nil {
		return err
	}
	rb, hb, err := readMarginalCSV(b)
	if err != nil {
		return err
	}
	for n := 0; n < MaxN; n++ {
		for t := 0; t < 6; t++ {
			oka := ha[n][t]
			okb := hb[n][t]
			if !oka && !okb {
				continue
			}
			if oka != okb {
				return fmt.Errorf("n=%d dice=%s: presence mismatch", n, DiceNames[t])
			}
			if math.Abs(ra[n][t]-rb[n][t]) > tol {
				return fmt.Errorf("n=%d dice=%s: go=%.4f c=%.4f diff=%.4f", n, DiceNames[t], ra[n][t], rb[n][t], ra[n][t]-rb[n][t])
			}
		}
	}
	return nil
}

func readMarginalCSV(path string) (map[int][6]float64, map[int][6]bool, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	rows, err := r.ReadAll()
	if err != nil {
		return nil, nil, err
	}
	vals := make(map[int][6]float64)
	has := make(map[int][6]bool)
	for _, row := range rows[1:] {
		n, _ := strconv.Atoi(row[0])
		vrow := vals[n]
		hrow := has[n]
		for t := 0; t < 6; t++ {
			if row[t+1] == "" {
				continue
			}
			vrow[t], _ = strconv.ParseFloat(row[t+1], 64)
			hrow[t] = true
		}
		vals[n] = vrow
		has[n] = hrow
	}
	return vals, has, nil
}
