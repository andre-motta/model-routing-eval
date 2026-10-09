#!/usr/bin/env bash
# Second replication of a grid: re-run every (model, effort) cell of a config's matrix with a
# run-id suffix, so eval-anova's --analyze-only sees two replications per condition.
#   ./replicate.sh eval.yaml r1
#   ./replicate.sh eval-codex.yaml r1
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=${1:?config}; REP=${2:-r1}
.venv/bin/python - "$CONFIG" "$REP" <<'PY' | while read -r model effort; do
import sys, yaml
cfg = sys.argv[1]
def load(p):
    import re
    txt = open(p).read().replace("!replace", "")
    return yaml.safe_load(txt)
c = load(cfg)
if "extends" in c:
    base = load(c["extends"].lstrip("./")); base.update({k: v for k, v in c.items() if k != "extends"}); c = base
f = c["matrix"]["factors"]
for m in f["model"]:
    for e in f["effort"]:
        print(m, e)
PY
  id="$(date +%Y-%m-%d)-$model-effort-$effort"
  RUN_ID="$id-$REP" ./run_eval.sh "$model" "$effort" "$CONFIG"
  # Runs sharing the same factor levels are treated as replications by eval-anova; reuse the
  # first pass's condition.json so the analyzer groups this run with its sibling.
  src=eval/runs/model-routing-eval/$id/condition.json
  [ -f "$src" ] && cp "$src" "eval/runs/model-routing-eval/$id-$REP/condition.json" && echo "condition.json copied for $id-$REP"
done
