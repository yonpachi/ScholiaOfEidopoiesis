package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/yonpachi/ScholiaOfEidopoiesis/sim/pkg/catalog"
)

func main() {
	dbPath := flag.String("catalog", "", "path to catalog/game.sqlite (default: auto-detect)")
	flag.Parse()

	cat, err := catalog.Open(*dbPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "open catalog: %v\n", err)
		os.Exit(1)
	}
	defer cat.Close()

	issues := cat.Validate()
	if len(issues) == 0 {
		fmt.Println("catalog validation: OK")
		return
	}

	fmt.Fprintf(os.Stderr, "catalog validation: %d issue(s)\n", len(issues))
	for _, issue := range issues {
		fmt.Fprintf(os.Stderr, "  %s\n", issue.Error())
	}
	os.Exit(1)
}
