package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/dice"
)

func main() {
	outDir := flag.String("out", "", "output directory (required)")
	seed := flag.Int64("seed", 42, "RNG seed for reproducibility")
	trials := flag.Int("trials", 5000, "trials per composition")
	flag.Parse()

	if flag.NArg() > 0 && *outDir == "" {
		*outDir = flag.Arg(0)
	}
	if *outDir == "" {
		fmt.Fprintln(os.Stderr, "error: -out directory required")
		os.Exit(1)
	}

	out := strings.TrimSuffix(filepath.Clean(*outDir), string(os.PathSeparator))
	if err := os.MkdirAll(out, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("=== Part2: full enumeration marginal (trials/comp=%d, max=%d) ===\n", *trials, dice.MaxN)
	if err := RunFullEnumeration(*trials, out, *seed); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
