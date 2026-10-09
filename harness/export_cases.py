#!/usr/bin/env python3
"""Generate eval/cases/<task>/ for agent-eval-harness from tasks/.

Each case gets input.yaml (prompt + task id, what the agent sees) and annotations.yaml
(tier, title, and for real-repo tasks the oracle diff path; judge-side only).
Run after adding or editing a task:  python harness/export_cases.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import TASKS, ROOT  # noqa: E402

CASES = ROOT / "eval" / "cases"


def main():
    CASES.mkdir(parents=True, exist_ok=True)
    n = 0
    for d in sorted(TASKS.iterdir()):
        if not (d / "task.yaml").exists():
            continue
        meta = yaml.safe_load((d / "task.yaml").read_text())
        case = CASES / d.name
        case.mkdir(exist_ok=True)
        (case / "input.yaml").write_text(yaml.safe_dump({"task": d.name, "prompt": (d / "prompt.md").read_text()},
                                                        sort_keys=False, width=1000))
        ann = {"tier": meta["tier"], "title": meta["title"], "category": f"tier{meta['tier']}"}
        if meta.get("ticket_only"):
            ann["ticket_only"] = True
            ann["variant_of"] = meta.get("variant_of")
        if meta.get("oracle"):
            src = meta["oracle"]
            if src.get("repo_dir") and src.get("range"):
                diff = subprocess.run(["git", "-C", str(Path(src["repo_dir"]).expanduser()), "diff", src["range"], "--", "src", "docs"],
                                      capture_output=True, text=True).stdout
                (case / "oracle.diff").write_text(diff)
                ann["oracle"] = "oracle.diff"
        (case / "annotations.yaml").write_text(yaml.safe_dump(ann, sort_keys=False))
        n += 1
    print(f"wrote {n} cases under {CASES}")


if __name__ == "__main__":
    main()
