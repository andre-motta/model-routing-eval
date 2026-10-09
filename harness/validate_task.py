#!/usr/bin/env python3
"""Validate a task: hidden tests must FAIL on the fixture and PASS at a known-good commit or with a patch.

  python harness/validate_task.py r01_fromager_distinfo --good-commit 3914e3e
"""
import argparse
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import prepare_workdir, verify, TASKS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--good-commit", help="commit where hidden tests should pass (source tasks)")
    args = ap.parse_args()
    d = TASKS / args.task
    meta = yaml.safe_load((d / "task.yaml").read_text()); meta["id"] = d.name; meta["dir"] = d

    work = prepare_workdir(meta, None)
    ok, out = verify(meta, work)
    print(f"[baseline] passed={ok}  (expected False)\n{out[-600:]}\n")
    shutil.rmtree(work, ignore_errors=True)

    if args.good_commit:
        good = dict(meta); good["source"] = dict(meta["source"], commit=args.good_commit)
        work = prepare_workdir(good, None)
        ok2, out2 = verify(good, work)
        print(f"[good commit {args.good_commit}] passed={ok2}  (expected True)\n{out2[-600:]}")
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
