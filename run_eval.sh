#!/usr/bin/env bash
# Headless agent-eval-harness pipeline for one (model, effort) configuration.
#   ./run_eval.sh <model> <effort> [eval.yaml|eval-codex.yaml] [case ...]
# Produces $AGENT_EVAL_RUNS_DIR/<name>/<run-id>/ with summary.yaml and report.html.
set -euo pipefail
cd "$(dirname "$0")"
MODEL=${1:?model}; EFFORT=${2:?effort}; CONFIG=${3:-eval.yaml}; shift 3 2>/dev/null || shift $#
CASES=("$@")
export AGENT_EVAL_RUNS_DIR=${AGENT_EVAL_RUNS_DIR:-$PWD/eval/runs}
# Workspaces go under TMPDIR/agent-eval. /tmp is RAM on some machines and a fromager case is ~120 MB,
# so keep them on disk and delete them once the run's artifacts are collected.
export TMPDIR=${EVAL_TMPDIR:-$PWD/.work}; mkdir -p "$TMPDIR"
# This machine's interactive Claude Code session runs on Vertex; the eval agent should use the
# caller's normal Claude Code auth (CLAUDE_CONFIG_DIR is forwarded by runner.env in eval.yaml).
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID CLOUD_ML_REGION
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=${AGENT_EVAL_PLUGIN:-$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")}
S="$PLUGIN/skills/eval-run/scripts"
PY=.venv/bin/python
RUN_ID=${RUN_ID:-$(date +%Y-%m-%d)-$(basename "$CONFIG" .yaml)-$MODEL-$EFFORT}
WS=$TMPDIR/agent-eval/$RUN_ID
# eval name comes from the nearest config in the extends chain that carries one (profiles like eval-codex.yaml have none)
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
OUT=$AGENT_EVAL_RUNS_DIR/$NAME/$RUN_ID
mkdir -p "$AGENT_EVAL_RUNS_DIR" tmp
echo "run-id $RUN_ID  config $CONFIG  model $MODEL  effort $EFFORT  cases ${CASES[*]:-all}"
$PY "$S/workspace.py" --config "$CONFIG" --run-id "$RUN_ID" ${CASES:+--cases "${CASES[@]}"}
$PY "$S/execute.py" --workspace "$WS" --config "$CONFIG" --model "$MODEL" --effort "$EFFORT" --output "$OUT" --run-id "$RUN_ID"
$PY "$S/collect.py" --config "$CONFIG" --workspace "$WS" --output "$OUT"
# score.py exits non-zero when a threshold regresses (e.g. a structural check fails); that is a result, not a pipeline error.
$PY "$S/score.py" judges --run-id "$RUN_ID" --config "$CONFIG" --workspace "$WS" --model "$MODEL" ${NO_LLM_JUDGES:+--no-llm-judges} || true
$PY "$S/report.py" --run-id "$RUN_ID" --config "$CONFIG" --title "$NAME $MODEL@$EFFORT" || true
[ -n "${KEEP_WORKSPACE:-}" ] || /bin/rm -rf "$WS"
echo "done: $OUT"
