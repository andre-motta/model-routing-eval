#!/usr/bin/env python3
"""Finish a run that was cut short: synthesize the top-level run_result.json from the per-case
results so collect/score/report can run on the cases that completed. Marks the run partial.

  python harness/finalize_partial.py <run-id> --template <complete-run-id>
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import ROOT  # noqa: E402

RUNS = Path(os.environ.get("AGENT_EVAL_RUNS_DIR", ROOT / "eval" / "runs")) / "model-routing-eval"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--template", required=True, help="a complete run with the same agent, to copy the envelope from")
    ap.add_argument("--model")
    ap.add_argument("--effort")
    a = ap.parse_args()
    run = RUNS / a.run_id
    T = json.loads((RUNS / a.template / "run_result.json").read_text())
    per_case, cost, dur, turns = {}, 0.0, 0.0, 0
    tokens = dict(input=0, output=0, cache_read=0, cache_create=0)
    for c in sorted((run / "cases").iterdir()):
        rr = c / "run_result.json"
        if not rr.exists():
            continue
        d = json.loads(rr.read_text())
        per_case[c.name] = d
        cost += d.get("cost_usd") or 0
        dur += d.get("duration_s") or 0
        turns += d.get("num_turns") or 0
        for k in tokens:
            tokens[k] += (d.get("token_usage") or {}).get(k, 0)
    R = {k: T.get(k) for k in ("agent", "agent_version", "execution_mode", "permission_denials", "message_ids")}
    R.update(exit_code=0, duration_s=dur, wall_clock_s=dur, cost_usd=cost, token_usage=tokens, num_turns=turns,
             per_model_usage={}, per_model_turns={}, num_cases=len(per_case), model=a.model or T.get("model"),
             eval_params=dict(T.get("eval_params") or {}, effort=a.effort or (T.get("eval_params") or {}).get("effort")),
             per_case=per_case, partial=True, note="run was cut short; only completed cases are included")
    (run / "run_result.json").write_text(json.dumps(R, indent=2))
    print(f"{a.run_id}: {len(per_case)} cases, ${cost:.3f}, marked partial")


if __name__ == "__main__":
    main()
