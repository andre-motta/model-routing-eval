#!/usr/bin/env bash
# Run the model x effort matrix of a config through agent-eval-harness's eval-anova orchestrator.
#   ./run_matrix.sh eval.yaml            # Anthropic grid
#   ./run_matrix.sh eval-codex.yaml      # OpenAI grid
#   DRY=1 ./run_matrix.sh eval.yaml      # design + cost estimate only
# Every cell is a normal /eval-run run under eval/runs/model-routing-eval/; anova.json and the
# /eval-compare report land under eval/runs/model-routing-eval/compare-<config>/.
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=${1:?config}; shift || true
export AGENT_EVAL_RUNS_DIR=${AGENT_EVAL_RUNS_DIR:-$PWD/eval/runs}
export TMPDIR=${EVAL_TMPDIR:-$PWD/.work}; mkdir -p "$TMPDIR"
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID CLOUD_ML_REGION
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")
OUT=$AGENT_EVAL_RUNS_DIR/model-routing-eval/compare-$(basename "$CONFIG" .yaml)
if [ -n "${DRY:-}" ]; then
  exec .venv/bin/python "$PLUGIN/skills/eval-anova/scripts/orchestrate.py" --config "$CONFIG" --dry-run --avg-cost-per-run "${AVG_COST:-0.15}" "$@"
fi
.venv/bin/python "$PLUGIN/skills/eval-anova/scripts/orchestrate.py" --config "$CONFIG" --output "$OUT" "$@"
/bin/rm -rf "$TMPDIR/agent-eval"
echo "matrix done: $OUT"
