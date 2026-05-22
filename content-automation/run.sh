#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG="$DIR/output/run.log"

mkdir -p "$DIR/output"

echo "--- $(date) ---" >> "$LOG"

cd "$DIR"

"$DIR/venv/bin/python" "$DIR/main.py" >> "$LOG" 2>&1
