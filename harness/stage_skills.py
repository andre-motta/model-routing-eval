#!/usr/bin/env python3
"""agent-eval-harness before_each hook: copy a plugin's skills into the case workspace for Codex.

The Codex runner stages ``runner.plugin_dirs`` skills under ``<workspace>/.agents/skills`` itself, but
refuses when the workspace already has a ``.agents/skills`` tree it does not own (the rhoai prototype
repo ships one). For those tasks the Codex profiles set ``plugin_dirs`` empty and run this hook instead:
it copies ``tasks/<task>/task.yaml:plugin``'s ``skills/*`` into ``.agents/skills/`` next to the repo's own
and excludes them from the git baseline so they never show up in solution.diff.
"""
import os
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import TASKS, ROOT  # noqa: E402


def main():
    work = Path(os.environ["CASE_WORKSPACE"])
    task_id = yaml.safe_load(Path(os.environ["CASE_INPUT"]).read_text())["task"]
    task = yaml.safe_load((TASKS / task_id / "task.yaml").read_text())
    plugin = task.get("plugin")
    if not plugin:
        print(f"{task_id}: no plugin to stage")
        return
    src = (ROOT / plugin / "skills").resolve()
    dest = work / ".agents" / "skills"
    dest.mkdir(parents=True, exist_ok=True)
    names = []
    for skill in sorted(p for p in src.iterdir() if (p / "SKILL.md").exists()):
        target = dest / skill.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill, target, symlinks=False)
        names.append(skill.name)
    exclude = work / ".git" / "info" / "exclude"
    if exclude.exists():
        with exclude.open("a") as f:
            for n in names:
                f.write(f".agents/skills/{n}/\n")
    print(f"staged {len(names)} skills into {dest}: {', '.join(names)}")


if __name__ == "__main__":
    main()
