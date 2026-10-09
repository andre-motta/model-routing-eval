#!/usr/bin/env bash
# Headless agent-eval-harness pipeline for one (model, effort) configuration.
#   ./run_eval.sh <model> <effort> [eval.yaml|eval-codex.yaml] [case ...]
# Produces $AGENT_EVAL_RUNS_DIR/<name>/<run-id>/ with summary.yaml and report.html.
set -euo pipefail
cd "$(dirname "$0")"
MODEL=${1:?model}; EFFORT=${2:?effort}; CONFIG=${3:-eval.yaml}; shift 3 2>/dev/null || shift $#
CASES=("$@")
export AGENT_EVAL_RUNS_DIR=${AGENT_EVAL_RUNS_DIR:-$PWD/eval/runs}
# This machine's interactive Claude Code session runs on Vertex; the eval agent should use the
# caller's normal Claude Code auth (CLAUDE_CONFIG_DIR is forwarded by runner.env in eval.yaml).
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID CLOUD_ML_REGION
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=${AGENT_EVAL_PLUGIN:-$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")}
S="$PLUGIN/skills/eval-run/scripts"
PY=.venv/bin/python
RUN_ID=${RUN_ID:-$(date +%Y-%m-%d)-$(basename "$CONFIG" .yaml)-$MODEL-$EFFORT}
WS=/tmp/agent-eval/$RUN_ID
# eval name comes from the root of the extends chain (profiles like eval-codex.yaml carry no name)
NAME=$(grep -h -m1 '^name:' "$CONFIG" eval.yaml | head -1 | sed 's/^name:[[:space:]]*//')
OUT=$AGENT_EVAL_RUNS_DIR/$NAME/$RUN_ID
mkdir -p "$AGENT_EVAL_RUNS_DIR" tmp
echo "run-id $RUN_ID  config $CONFIG  model $MODEL  effort $EFFORT  cases ${CASES[*]:-all}"
$PY "$S/workspace.py" --config "$CONFIG" --run-id "$RUN_ID" ${CASES:+--cases "${CASES[@]}"}
$PY "$S/execute.py" --workspace "$WS" --config "$CONFIG" --model "$MODEL" --effort "$EFFORT" --output "$OUT" --run-id "$RUN_ID"
$PY "$S/collect.py" --config "$CONFIG" --workspace "$WS" --output "$OUT"
$PY "$S/score.py" judges --run-id "$RUN_ID" --config "$CONFIG" --workspace "$WS" --model "$MODEL" ${NO_LLM_JUDGES:+--no-llm-judges}
$PY "$S/report.py" --run-id "$RUN_ID" --config "$CONFIG" --title "$NAME $MODEL@$EFFORT" || true
echo "done: $OUT"
