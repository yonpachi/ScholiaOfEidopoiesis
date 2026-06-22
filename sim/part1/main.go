package main

import (
	"flag"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	outDir := flag.String("out", "", "output directory (optional CSV)")
	seed := flag.Int64("seed", 42, "RNG seed")
	trials := flag.Int("trials", 20000, "trials per pool")
	flag.Parse()

	if flag.NArg() > 0 && *outDir == "" {
		*outDir = flag.Arg(0)
	}

	rng := rand.New(rand.NewSource(*seed))
	out := ""
	if *outDir != "" {
		out = strings.TrimSuffix(filepath.Clean(*outDir), string(os.PathSeparator))
	}
	if err := RunPart1Reference(*trials, out, rng); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
