#!/usr/bin/env python3
"""Re-run the hidden tests for finished harness cases from their saved solution.diff.

Use after a hidden test changes:  python harness/reverify.py <run-id> [case ...]
Rebuilds the fixture (or repo checkout plus setup), applies output/solution.diff, runs the verifier,
rewrites output/tests.json and output/verify.log in the run directory. Re-score afterwards with ./rescore.sh.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import TASKS, ROOT, prepare_workdir, verify  # noqa: E402

RUNS = Path(os.environ.get("AGENT_EVAL_RUNS_DIR", ROOT / "eval" / "runs")) / "model-routing-eval"


def main():
    run_id = sys.argv[1]
    cases = sys.argv[2:] or [p.name for p in (RUNS / run_id / "cases").iterdir() if (p / "output" / "solution.diff").exists()]
    for case_id in cases:
        out = RUNS / run_id / "cases" / case_id / "output"
        d = TASKS / case_id
        task = yaml.safe_load((d / "task.yaml").read_text()); task["id"] = case_id; task["dir"] = d
        if task.get("ticket_only"):
            print(f"{case_id}: ticket-only, nothing to verify"); continue
        work = prepare_workdir(task, None)
        diff = (out / "solution.diff").read_text()
        if diff.strip():
            r = subprocess.run(["git", "apply", "--whitespace=nowarn", "-"], cwd=work, input=diff, capture_output=True, text=True)
            if r.returncode != 0:
                print(f"{case_id}: patch did not apply: {r.stderr[-300:]}"); shutil.rmtree(work, ignore_errors=True); continue
        passed, log = verify(task, work)
        (out / "verify.log").write_text(log)
        (out / "tests.json").write_text(json.dumps({"passed": passed, "task": case_id, "tier": task.get("tier"), "reverified": True}))
        shutil.rmtree(work, ignore_errors=True)
        print(f"{case_id}: passed={passed}")


if __name__ == "__main__":
    main()
