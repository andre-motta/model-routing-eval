#!/usr/bin/env python3
"""Measure the harness tax: tokens and cost of a one-word answer in a fresh session, per backend and model.

  python harness/overhead.py --backend claude --models claude-haiku-5-5 claude-sonnet-5-5 claude-opus-5-5
  python harness/overhead.py --backend codex  --models gpt-6-luna gpt-6.1-sol
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.pricing import cost_usd, resolve  # noqa: E402

PROMPT = "Reply with exactly: OK"


def claude(model, effort, cwd):
    p = subprocess.run(["claude", "-p", PROMPT, "--model", model, "--effort", effort, "--output-format", "json",
                        "--max-turns", "1", "--permission-mode", "plan", "--no-session-persistence"],
                       cwd=cwd, capture_output=True, text=True, timeout=300)
    d = json.loads(p.stdout)
    u = d["usage"]
    tokens = dict(input=u.get("input_tokens", 0), cached=u.get("cache_read_input_tokens", 0),
                  cache_write=u.get("cache_creation_input_tokens", 0), output=u.get("output_tokens", 0))
    return tokens, d.get("total_cost_usd"), d.get("duration_ms", 0) / 1000


def codex(model, effort, cwd):
    p = subprocess.run(["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-C", cwd, "-s", "read-only",
                        "-m", model, "-c", f'model_reasoning_effort="{effort}"', PROMPT],
                       capture_output=True, text=True, timeout=300)
    tokens = dict(input=0, cached=0, cache_write=0, output=0)
    for line in p.stdout.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "turn.completed":
            u = e["usage"]
            tokens["cached"] += u.get("cached_input_tokens", 0)
            tokens["input"] += u.get("input_tokens", 0) - u.get("cached_input_tokens", 0)
            tokens["cache_write"] += u.get("cache_write_input_tokens", 0)
            tokens["output"] += u.get("output_tokens", 0)
    return tokens, cost_usd(model, tokens), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["claude", "codex"], required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--effort", default="low")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    fn = claude if args.backend == "claude" else codex
    rows = []
    with tempfile.TemporaryDirectory() as cwd:
        print(f"{'model':28} {'uncached':>9} {'cached':>8} {'cache_w':>8} {'output':>7} {'cost':>8}")
        for m in args.models:
            m = resolve(m)
            tokens, cost, secs = fn(m, args.effort, cwd)
            rows.append(dict(backend=args.backend, model=m, effort=args.effort, tokens=tokens, cost_usd=cost, wall_s=secs))
            print(f"{m:28} {tokens['input']:>9} {tokens['cached']:>8} {tokens['cache_write']:>8} {tokens['output']:>7} "
                  f"${(cost or 0):>7.4f}")
    if args.out:
        Path(args.out).write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
