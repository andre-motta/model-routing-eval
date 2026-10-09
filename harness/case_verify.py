#!/usr/bin/env python3
"""agent-eval-harness after_each hook: run the hidden tests and write output/tests.json.

Also captures the agent's diff as output/solution.diff and the verifier log as output/verify.log,
so the `tests_pass` check judge and the LLM judge can read them from the collected outputs.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import TASKS, verify  # noqa: E402


def main():
    work = Path(os.environ["CASE_WORKSPACE"])
    task_id = yaml.safe_load(Path(os.environ["CASE_INPUT"]).read_text())["task"]
    d = TASKS / task_id
    task = yaml.safe_load((d / "task.yaml").read_text())
    task["id"] = task_id
    task["dir"] = d
    out = work / "output"
    out.mkdir(exist_ok=True)
    subprocess.run(["git", "add", "-A", "--", ".", ":!hidden", ":!output"], cwd=work, capture_output=True)
    diff = subprocess.run(["git", "diff", "--cached", "--", ".", ":!hidden", ":!output"], cwd=work,
                          capture_output=True, text=True).stdout
    (out / "solution.diff").write_text(diff)
    if task.get("ticket_only"):
        passed, log = None, "ticket-only variant: hidden tests not applicable, scored by the LLM judge"
    else:
        try:
            passed, log = verify(task, work)
        except Exception as e:  # noqa: BLE001
            passed, log = False, f"verifier error: {e}"
    (out / "verify.log").write_text(log)
    (out / "tests.json").write_text(json.dumps({"passed": passed, "task": task_id, "tier": task.get("tier")}))
    print(f"verified {task_id}: passed={passed}")


if __name__ == "__main__":
    main()
