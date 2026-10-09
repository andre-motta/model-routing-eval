#!/usr/bin/env python3
"""Re-price Codex cases from harness/pricing.py (list prices), independent of LiteLLM.

Used as an agent-eval-harness `before_scoring` hook (env: AGENT_EVAL_RUNS_DIR, AGENT_EVAL_RUN_ID,
AGENT_EVAL_CONFIG) or by hand:  python harness/price_runs.py eval/runs/model-routing-eval/<run-id>

Only cases whose agent is codex and whose model is in PRICES are touched. Claude Code reports its
own cost. The original value is kept as cost_usd_litellm; cost_source becomes "pricing-table".
"""
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.pricing import PRICES, cost_usd, resolve  # noqa: E402


def price_case(rr: Path, model: str) -> float | None:
    d = json.loads(rr.read_text())
    tk = d.get("token_usage") or {}
    # Codex reports input inclusive of cached reads; our table wants uncached input separately.
    tokens = dict(input=max(0, tk.get("input", 0) - tk.get("cache_read", 0)), cached=tk.get("cache_read", 0),
                  cache_write=tk.get("cache_create", 0), output=tk.get("output", 0))
    c = cost_usd(model, tokens)
    if c is None:
        return None
    if d.get("cost_usd") not in (None, c):
        d["cost_usd_litellm"] = d.get("cost_usd")
    d["cost_usd"] = round(c, 6)
    d["cost_source"] = "pricing-table"
    rr.write_text(json.dumps(d, indent=2))
    return c


def main():
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1])
    else:
        cfg = Path(os.environ["AGENT_EVAL_CONFIG"])
        name = next(ln.split(":", 1)[1].strip() for ln in (cfg.parent / "eval.yaml").read_text().splitlines() if ln.startswith("name:"))
        run_dir = Path(os.environ.get("AGENT_EVAL_RUNS_DIR", "eval/runs")) / name / os.environ["AGENT_EVAL_RUN_ID"]
    top = run_dir / "run_result.json"
    if not top.exists():
        print(f"price_runs: no run_result.json under {run_dir}, nothing to do")
        return
    R = json.loads(top.read_text())
    if R.get("agent") != "codex" or resolve(R.get("model") or "") not in PRICES:
        print(f"price_runs: agent={R.get('agent')} model={R.get('model')}, leaving costs as reported")
        return
    model = resolve(R["model"])
    total = 0.0
    for case_id in (R.get("per_case") or {}):
        rr = run_dir / "cases" / case_id / "run_result.json"
        if rr.exists():
            c = price_case(rr, model)
            if c is not None:
                R["per_case"][case_id]["cost_usd"] = round(c, 6)
                total += c
    R["cost_usd_litellm"] = R.get("cost_usd")
    R["cost_usd"] = round(total, 6)
    R["cost_source"] = "pricing-table"
    top.write_text(json.dumps(R, indent=2))
    print(f"price_runs: {model}: {len(R.get('per_case') or {})} cases re-priced, total ${total:.4f}")


if __name__ == "__main__":
    main()
