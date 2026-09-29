#!/usr/bin/env bash
# Run every part of experiment 005 against a git repository.
#   ./run.sh ~/code/wgh            # results land in ./results
#   ./run.sh ~/code/wgh /tmp/out   # or somewhere else
set -euo pipefail
REPO="$(cd "${1:?usage: ./run.sh PATH_TO_REPO [RESULTS_DIR]}" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${2:-$HERE/results}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
cd "$HERE"
python3 scan_violations.py --repo "$REPO" --out "$OUT"
python3 git_events.py --repo "$REPO" --out "$OUT/events.jsonl"
python3 replay.py --events "$OUT/events.jsonl" --out "$OUT"
python3 replay.py --events "$OUT/events.jsonl" --out "$OUT" --runs-per-day 20 --tag _20perday
python3 rule_lifecycle.py --repo "$REPO" --results "$OUT"
python3 counterfactual.py --repo "$REPO" --results "$OUT"
