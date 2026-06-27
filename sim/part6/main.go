package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	outDir := flag.String("out", "", "output directory (required)")
	seed := flag.Int64("seed", 42, "RNG seed")
	trials := flag.Int("trials", 50000, "campaigns per n_extra")
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

	if err := RunQualityProgression(*trials, out, *seed); err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
