#!/usr/bin/env bash
# Run the model x effort matrix of a config through agent-eval-harness's eval-anova orchestrator.
#   ./run_matrix.sh eval.yaml            # Anthropic grid
#   ./run_matrix.sh eval-codex.yaml      # OpenAI grid
#   DRY=1 ./run_matrix.sh eval.yaml      # design + cost estimate only
# Every cell is a normal /eval-run run under eval/runs/<name>/ (name from the config's extends chain);
# anova.json and the /eval-compare report land under eval/runs/<name>/compare-<config>/.
# Set EVAL_TMPDIR to a distinct dir when running two matrices at once (the workspace dir is wiped at the end).
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=${1:?config}; shift || true
export AGENT_EVAL_RUNS_DIR=${AGENT_EVAL_RUNS_DIR:-$PWD/eval/runs}
export TMPDIR=${EVAL_TMPDIR:-$PWD/.work}; mkdir -p "$TMPDIR"
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID CLOUD_ML_REGION
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")
NAME=$(.venv/bin/python - "$CONFIG" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
while True:
    txt = p.read_text()
    name = next((l.split(":", 1)[1].strip() for l in txt.splitlines() if l.startswith("name:")), None)
    if name:
        print(name); break
    ext = next((l.split(":", 1)[1].strip() for l in txt.splitlines() if l.startswith("extends:")), None)
    if not ext:
        print("model-routing-eval"); break
    p = (p.parent / ext).resolve()
PY
)
OUT=$AGENT_EVAL_RUNS_DIR/$NAME/compare-$(basename "$CONFIG" .yaml)
if [ -n "${DRY:-}" ]; then
  exec .venv/bin/python "$PLUGIN/skills/eval-anova/scripts/orchestrate.py" --config "$CONFIG" --dry-run --avg-cost-per-run "${AVG_COST:-0.15}" "$@"
fi
.venv/bin/python "$PLUGIN/skills/eval-anova/scripts/orchestrate.py" --config "$CONFIG" --output "$OUT" "$@"
/bin/rm -rf "$TMPDIR/agent-eval"
echo "matrix done: $OUT"
