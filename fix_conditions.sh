#!/usr/bin/env bash
# Copy condition.json from each first-pass cell to its -r<N> replications that lack one.
cd "$(dirname "$0")/eval/runs/model-routing-eval"
for d in *-r[0-9]*/; do d=${d%/}; base=${d%-r*}; [ -f "$d/condition.json" ] && continue; [ -f "$base/condition.json" ] && cp "$base/condition.json" "$d/" && echo "copied -> $d"; done
