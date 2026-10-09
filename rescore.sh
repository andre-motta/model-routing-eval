#!/usr/bin/env bash
# Re-run the judges (and the HTML report) for every run under eval/runs/model-routing-eval,
# e.g. after changing the judge model in eval.yaml. Deterministic judges are free; LLM judge calls cost.
#   ./rescore.sh            # all runs
#   ./rescore.sh <run-id>…  # selected runs
set -euo pipefail
cd "$(dirname "$0")"
export AGENT_EVAL_RUNS_DIR=${AGENT_EVAL_RUNS_DIR:-$PWD/eval/runs}
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID CLOUD_ML_REGION
export CLAUDE_CONFIG_DIR=${CLAUDE_CONFIG_DIR:-$HOME/.claude}
PLUGIN=$(.venv/bin/python -c "import agent_eval, pathlib; print(pathlib.Path(agent_eval.__file__).resolve().parents[1])")
S="$PLUGIN/skills/eval-run/scripts"
RUNS=$AGENT_EVAL_RUNS_DIR/model-routing-eval
if [ $# -gt 0 ]; then IDS=("$@"); else IDS=($(ls "$RUNS" | grep -v '^compare-')); fi
for id in "${IDS[@]}"; do
  [ -f "$RUNS/$id/run_result.json" ] || continue
  # Always judge with eval.yaml: its runner is claude-code, so the runner:/claude-opus-5-5 judge works for
  # Codex and GLM runs too (a runner:/ judge inside a Codex profile would try to run Opus through Codex).
  cfg=eval.yaml
  model=$(.venv/bin/python -c "import json;print(json.load(open('$RUNS/$id/run_result.json'))['model'])")
  echo "== rescoring $id ($model)"
  .venv/bin/python "$S/score.py" judges --run-id "$id" --config "$cfg" --model "$model" 2>&1 | grep -E "pass_rate|mean=|judge_cost|rror" || true
  .venv/bin/python "$S/report.py" --run-id "$id" --config "$cfg" --title "model-routing-eval $id" >/dev/null 2>&1 || true
done
