#!/usr/bin/env bash
# Full experiment matrix. Run one block at a time; every run is skipped if its record exists.
# Dry run first:  DRY=--dry-run ./matrix.sh openai
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
DRY=${DRY:-}
R="$PY harness/run.py $DRY"

openai() {
  # Luna: cheap, 3 reps, every effort that matters
  for e in low medium xhigh; do $R --backend codex --model gpt-6-luna --effort $e --all --reps 3 --tag openai; done
  # Sol 6.1: the thinker; 3 reps
  for e in low medium high xhigh; do $R --backend codex --model gpt-6.1-sol --effort $e --all --reps 3 --tag openai; done
  # Terra 5.6: 1 rep, to show it is never the cheapest passing config
  for e in medium high; do $R --backend codex --model gpt-5.6-terra --effort $e --all --reps 1 --tag openai; done
  # Astra: 1 rep, hard tiers only
  for e in medium high; do $R --backend codex --model gpt-6-astra --effort $e --tier 3 4 5 --reps 1 --tag openai; done
}

anthropic() {
  for e in low medium xhigh; do $R --backend claude --model claude-haiku-5-5 --effort $e --all --reps 3 --tag anthropic; done
  for e in low medium high xhigh; do $R --backend claude --model claude-sonnet-5-5 --effort $e --all --reps 3 --tag anthropic; done
  for e in medium high; do $R --backend claude --model claude-opus-5-5 --effort $e --all --reps 1 --tag anthropic; done
  for e in medium high; do $R --backend claude --model claude-fable-5-1 --effort $e --tier 3 4 5 --reps 1 --tag anthropic; done
}

case "${1:-}" in
  openai) openai ;;
  anthropic) anthropic ;;
  *) echo "usage: [DRY=--dry-run] ./matrix.sh openai|anthropic"; exit 1 ;;
esac
