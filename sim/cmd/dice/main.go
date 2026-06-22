package main

import (
	"flag"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strings"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/pkg/dice"
)

func main() {
	outDir := flag.String("out", "", "output directory")
	seed := flag.Int64("seed", 42, "RNG seed for reproducibility")
	trials := flag.Int("trials", 10000, "trials per composition (Part2)")
	part1Trials := flag.Int("part1-trials", 20000, "trials for Part1 reference")
	windHalf := flag.Bool("wind-halfturn", true, "use WIND_HALFTURN (default); false = WIND_INVERT")
	part := flag.String("part", "all", "which part to run: 1, 2, or all")
	flag.Parse()

	if flag.NArg() > 0 && *outDir == "" {
		*outDir = flag.Arg(0)
	}

	wind := dice.WindHalfTurn
	if !*windHalf {
		wind = dice.WindInvert
	}

	rng := rand.New(rand.NewSource(*seed))

	runPart1 := *part == "all" || *part == "1"
	runPart2 := *part == "all" || *part == "2"

	if runPart1 {
		dice.RunPart1Reference(*part1Trials, wind, rng)
	}

	if runPart2 {
		if *outDir == "" {
			fmt.Fprintln(os.Stderr, "error: -out directory required for Part2")
			os.Exit(1)
		}
		out := strings.TrimSuffix(filepath.Clean(*outDir), string(os.PathSeparator))
		if err := os.MkdirAll(out, 0o755); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("\n=== Part2: full enumeration marginal (trials/comp=%d, max=%d) ===\n", *trials, dice.MaxN)
		if err := dice.RunFullEnumeration(*trials, wind, out, rng); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			os.Exit(1)
		}
	}
}
