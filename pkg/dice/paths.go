package dice

import (
	"os"
	"path/filepath"
)

const CSVSubdir = "csv"

// CSVDir returns the CSV output subdirectory under a run folder.
func CSVDir(outDir string) string {
	return filepath.Join(outDir, CSVSubdir)
}

// EnsureCSVDir creates outDir/csv and returns its path.
func EnsureCSVDir(outDir string) (string, error) {
	dir := CSVDir(outDir)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	return dir, nil
}
