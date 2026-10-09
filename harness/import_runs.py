#!/usr/bin/env python3
"""Import agent-eval-harness runs into the standalone record format so analyze.py and the deck
generator can read them.

  python harness/import_runs.py eval/runs/model-routing-eval --out results/harness

One JSON record per (run, case). Pass/fail comes from the tests_pass judge; ticket-only
cases carry the LLM judge score instead and count as passed when it is >= 4.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import ROOT  # noqa: E402

CASES = ROOT / "eval" / "cases"


def tier_of(case_id):
    p = CASES / case_id / "annotations.yaml"
    return yaml.safe_load(p.read_text()).get("tier") if p.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir")
    ap.add_argument("--out", default=str(ROOT / "results" / "harness"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for run in sorted(Path(args.runs_dir).iterdir()):
        rr = run / "run_result.json"
        sm = run / "summary.yaml"
        if not rr.exists():
            continue
        # pilot smoke runs duplicate grid cases on a handful of tasks; keep only the ticket-only pilots (extra judged runs)
        if run.name.startswith("smoke") and "tickets" not in run.name:
            continue
        R = json.loads(rr.read_text())
        S = yaml.safe_load(sm.read_text()) if sm.exists() else {}
        per_judge = S.get("per_case", {})
        model, agent = R.get("model"), R.get("agent", "claude-code")
        effort = (R.get("eval_params") or {}).get("effort") or "default"
        rep = 0
        m = re.search(r"-r(\d+)$", run.name)
        if m:
            rep = int(m.group(1))
        for case_id, c in (R.get("per_case") or {}).items():
            j = per_judge.get(case_id, {})
            tp = j.get("tests_pass", {}).get("value")
            sq = j.get("solution_quality", {}).get("value")
            passed = bool(tp) if tp is not None else (sq is not None and sq >= 4)
            tk = c.get("token_usage") or {}
            rec = dict(task=case_id, tier=tier_of(case_id), backend="codex" if agent == "codex" else "claude",
                       model=model, effort=effort, rep=rep, passed=passed, quality=sq,
                       verify_tail=j.get("tests_pass", {}).get("rationale", ""), run_id=run.name,
                       wall_s=c.get("duration_s") or c.get("wall_clock_s") or 0,
                       tokens=dict(input=tk.get("input", 0), cached=tk.get("cache_read", 0),
                                   cache_write=tk.get("cache_create", 0), output=tk.get("output", 0), reasoning=0),
                       turns=c.get("num_turns", 0), cost_usd=c.get("cost_usd"), error=c.get("error_class"))
            safe = (model or "unknown").replace("/", "_")
            (out / f"{case_id}__{safe}__{effort}__{run.name}.json").write_text(json.dumps(rec, indent=1))
            n += 1
    print(f"imported {n} case records into {out}")


if __name__ == "__main__":
    main()
