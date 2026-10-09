#!/usr/bin/env python3
"""agent-eval-harness before_each hook: materialize the task fixture into the case workspace.

Reads CASE_INPUT (input.yaml with a `task` field) and CASE_WORKSPACE from the environment,
copies tasks/<task>/fixture or the task's `source` checkout into the workspace, runs the
task's setup commands, and leaves a git baseline so the diff can be captured afterwards.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import TASKS, materialize_source, git  # noqa: E402


def main():
    work = Path(os.environ["CASE_WORKSPACE"])
    task_id = yaml.safe_load(Path(os.environ["CASE_INPUT"]).read_text())["task"]
    d = TASKS / task_id
    task = yaml.safe_load((d / "task.yaml").read_text())
    task["id"] = task_id
    task["dir"] = d
    if task.get("source"):
        materialize_source(task, work)
    if (d / "fixture").exists():
        shutil.copytree(d / "fixture", work, dirs_exist_ok=True)
    for cmd in task.get("setup", []):
        r = subprocess.run(cmd, shell=True, cwd=work, capture_output=True, text=True, timeout=1200)
        if r.returncode != 0:
            sys.exit(f"setup failed: {cmd}\n{r.stderr[-800:]}")
    if not (work / ".git").exists():
        git(work, "init", "-q")
    (work / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (work / ".git" / "info" / "exclude").write_text(".venv/\nhidden/\noutput/\n.claude/\ninput.yaml\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "fixture", "--allow-empty")
    print(f"prepared {task_id} in {work}")


if __name__ == "__main__":
    main()
