#!/usr/bin/env bash
# ANOVA + compare report over the matrix cells of one config, isolated from standalone runs.
#   ./anova.sh eval.yaml          # Anthropic grid (all replications present under eval/runs)
#   ./anova.sh eval-codex.yaml    # OpenAI grid
# The orchestrator groups every run under the runs dir into conditions; standalone runs (Opus,
# Astra, Terra, smoke) would become extra conditions with missing cases, so this builds a view
# containing only runs that carry condition.json for this config's factors.
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=${1:?config}
NAME=model-routing-eval
SRC=$PWD/eval/runs/$NAME
VIEW=$PWD/eval/anova/$(basename "$CONFIG" .yaml)
/bin/rm -rf "$VIEW"; mkdir -p "$VIEW/$NAME"
MODELS=$(.venv/bin/python - "$CONFIG" <<'PY'
import sys, yaml
def load(p):
    return yaml.safe_load(open(p).read().replace("!replace", ""))
c = load(sys.argv[1])
if "extends" in c:
    b = load(c["extends"].lstrip("./")); b.update({k: v for k, v in c.items() if k != "extends"}); c = b
print(" ".join(c["matrix"]["factors"]["model"]))
PY
)
n=0
for d in "$SRC"/*/; do
  [ -f "$d/condition.json" ] || continue
  m=$(.venv/bin/python -c "import json;print(json.load(open('$d/run_result.json'))['model'])")
  case " $MODELS " in *" $m "*) ln -s "$d" "$VIEW/$NAME/$(basename "$d")"; n=$((n+1));; esac
done
echo "anova view: $n runs for models [$MODELS]"
unset CLAUDE_CODE_USE_VERTEX; export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")
AGENT_EVAL_RUNS_DIR=$VIEW .venv/bin/python "$PLUGIN/skills/eval-anova/scripts/orchestrate.py" --config "$CONFIG" --analyze-only --output "$VIEW/compare" "${@:2}"
echo "report: $VIEW/compare"
