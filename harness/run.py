#!/usr/bin/env python3
"""Run the task matrix through a coding agent and record pass/fail, tokens, cost, time.

Examples:
  python harness/run.py --backend codex  --model gpt-6-luna --effort xhigh --tier 1 2 --reps 1
  python harness/run.py --backend claude --model claude-sonnet-5 --effort medium --all --dry-run
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.pricing import cost_usd, resolve  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"

# Rough upper bounds used only by --dry-run, from pilot runs. Tokens per run.
DRY_RUN_TOKENS = {1: dict(input=60_000, output=4_000), 2: dict(input=120_000, output=10_000),
                  3: dict(input=150_000, output=12_000), 4: dict(input=300_000, output=25_000),
                  5: dict(input=500_000, output=15_000)}


def load_tasks(args):
    tasks = []
    for d in sorted(TASKS.iterdir()):
        if not (d / "task.yaml").exists():
            continue
        meta = yaml.safe_load((d / "task.yaml").read_text())
        meta["id"] = d.name
        meta["dir"] = d
        if args.all or (args.tier and meta["tier"] in args.tier) or (args.tasks and d.name in args.tasks):
            tasks.append(meta)
    return tasks


def git(cwd, *a):
    subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "eval", "GIT_AUTHOR_EMAIL": "eval@example.com",
                        "GIT_COMMITTER_NAME": "eval", "GIT_COMMITTER_EMAIL": "eval@example.com"})


CACHE = ROOT / ".cache" / "repos"


def materialize_source(task, work):
    """task.yaml `source: {repo: <url>, commit: <sha>}` checks out that commit into work (no history)."""
    src = task["source"]
    CACHE.mkdir(parents=True, exist_ok=True)
    parts = src["repo"].rstrip("/").replace(":", "/").split("/")
    name = "__".join(parts[-2:]).removesuffix(".git")  # owner__repo, so forks do not collide
    cache = CACHE / name
    if not cache.exists():
        subprocess.run(["git", "clone", "-q", "--bare", src["repo"], str(cache)], check=True)
    have = subprocess.run(["git", "-C", str(cache), "cat-file", "-e", src["commit"] + "^{commit}"], capture_output=True)
    if have.returncode != 0:
        subprocess.run(["git", "-C", str(cache), "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*"], check=True)
    tar = subprocess.run(["git", "-C", str(cache), "archive", src["commit"]], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(work)], input=tar, check=True)


def prepare_workdir(task, keep_root):
    work = Path(tempfile.mkdtemp(prefix=f"{task['id']}_", dir=keep_root))
    if task.get("source"):
        materialize_source(task, work)
    if (task["dir"] / "fixture").exists():
        shutil.copytree(task["dir"] / "fixture", work, dirs_exist_ok=True)
    for cmd in task.get("setup", []):
        r = subprocess.run(cmd, shell=True, cwd=work, capture_output=True, text=True, timeout=1200)
        if r.returncode != 0:
            raise RuntimeError(f"setup failed for {task['id']}: {cmd}\n{r.stderr[-800:]}")
    git(work, "init", "-q")
    (work / ".git" / "info" / "exclude").write_text(".venv/\nhidden/\n")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "fixture", "--allow-empty")
    return work


def run_codex(prompt, work, model, effort, timeout):
    cmd = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
           "-C", str(work), "-s", "workspace-write", "-c", 'approval_policy="never"',
           "-m", model, "-c", f'model_reasoning_effort="{effort}"', prompt]
    t0 = time.time()
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    wall = time.time() - t0
    tokens = dict(input=0, cached=0, cache_write=0, output=0, reasoning=0)
    turns, errors, commands = 0, [], 0
    for line in p.stdout.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = e.get("type")
        if t == "turn.completed":
            u = e.get("usage", {})
            turns += 1
            tokens["cached"] += u.get("cached_input_tokens", 0)
            tokens["input"] += u.get("input_tokens", 0) - u.get("cached_input_tokens", 0)
            tokens["cache_write"] += u.get("cache_write_input_tokens", 0)
            tokens["output"] += u.get("output_tokens", 0)
            tokens["reasoning"] += u.get("reasoning_output_tokens", 0)
        elif t == "item.completed":
            it = e.get("item", {})
            if it.get("type") == "command_execution":
                commands += 1
            elif it.get("type") == "error" and "ultrafast" not in it.get("message", ""):
                errors.append(it.get("message", "")[:300])
        elif t == "error":
            errors.append(e.get("message", "")[:300])
    return dict(wall_s=wall, tokens=tokens, turns=commands or turns, cost_usd=cost_usd(model, tokens),
                error="; ".join(errors) or None, exit_code=p.returncode, stderr_tail=p.stderr[-2000:])


def run_claude(prompt, work, model, effort, timeout):
    cmd = ["claude", "-p", prompt, "--model", model, "--effort", effort, "--output-format", "json",
           "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Edit,Write,MultiEdit,Glob,Grep",
           "--max-turns", "80", "--no-session-persistence"]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    wall = time.time() - t0
    tokens = dict(input=0, cached=0, cache_write=0, output=0, reasoning=0)
    cost, turns, err = None, 0, None
    try:
        d = json.loads(p.stdout)
        u = d.get("usage", {})
        tokens["input"] = u.get("input_tokens", 0)
        tokens["cached"] = u.get("cache_read_input_tokens", 0)
        tokens["cache_write"] = u.get("cache_creation_input_tokens", 0)
        tokens["output"] = u.get("output_tokens", 0)
        tokens["reasoning"] = u.get("output_tokens_details", {}).get("thinking_tokens", 0)
        cost = d.get("total_cost_usd")
        turns = d.get("num_turns", 0)
        if d.get("is_error"):
            err = str(d.get("result"))[:300]
    except json.JSONDecodeError:
        err = f"unparseable output: {p.stdout[-300:]} {p.stderr[-300:]}"
    return dict(wall_s=wall, tokens=tokens, turns=turns, cost_usd=cost if cost is not None else cost_usd(model, tokens),
                error=err, exit_code=p.returncode, stderr_tail=p.stderr[-2000:])


BACKENDS = {"codex": run_codex, "claude": run_claude}


def verify(task, work):
    """Copy hidden/ into `hidden_dest` (default hidden/), then run `verify` from task.yaml or pytest on hidden/."""
    hidden = task["dir"] / "hidden"
    dest = work / task.get("hidden_dest", "hidden")
    if task.get("hidden_dest"):
        shutil.copytree(hidden, dest, dirs_exist_ok=True)
    else:
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(hidden, dest)
    custom = task["dir"] / "verify.sh"
    if task.get("verify"):
        cmd, shell = task["verify"], True
    elif custom.exists():
        cmd, shell = ["bash", str(custom)], False
    else:
        cmd, shell = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "hidden"], False
    # 6 GB cap on the verifier: a pathological solution (e.g. exhaustive search in the resolver task) must fail, not starve the host.
    import resource
    def _cap():
        resource.setrlimit(resource.RLIMIT_AS, (6 * 1024 ** 3, 6 * 1024 ** 3))
    p = subprocess.run(cmd, cwd=work, shell=shell, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=1200, preexec_fn=_cap)
    return p.returncode == 0, (p.stdout + p.stderr)[-3000:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=BACKENDS, required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", required=True)
    ap.add_argument("--tier", type=int, nargs="*")
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=1200)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--tag", default=None, help="results subfolder, default <backend>")
    ap.add_argument("--keep-work", action="store_true", help="keep agent work dirs under results/<tag>/work")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    model = resolve(args.model)
    tasks = load_tasks(args)
    if not tasks:
        sys.exit("no tasks selected: use --all, --tier N, or --tasks id ...")
    out = Path(args.out) / (args.tag or args.backend)
    out.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        total = 0.0
        print(f"{'task':28} tier  est_cost_per_run")
        for t in tasks:
            est = cost_usd(model, DRY_RUN_TOKENS[t["tier"]]) or 0.0
            total += est * args.reps
            print(f"{t['id']:28} {t['tier']:>4}  ${est:.3f}")
        print(f"\n{len(tasks)} tasks x {args.reps} reps on {model}@{args.effort}: upper bound about ${total:.2f}")
        return

    keep_root = out / "work" if args.keep_work else None
    if keep_root:
        keep_root.mkdir(exist_ok=True)

    for t in tasks:
        for rep in range(args.reps):
            name = f"{t['id']}__{model}__{args.effort}__r{rep}"
            rec_path = out / f"{name}.json"
            if rec_path.exists():
                print(f"skip {name} (exists)")
                continue
            work = prepare_workdir(t, keep_root)
            prompt = (t["dir"] / "prompt.md").read_text()
            print(f"run  {name} ...", end="", flush=True)
            try:
                r = BACKENDS[args.backend](prompt, work, model, args.effort, min(args.timeout, t.get("timeout", args.timeout)))
            except subprocess.TimeoutExpired:
                r = dict(wall_s=args.timeout, tokens={}, turns=0, cost_usd=None, error="timeout", exit_code=None, stderr_tail="")
            passed, vout = verify(t, work)
            subprocess.run(["git", "add", "-A", "--", ".", ":!hidden"], cwd=work, capture_output=True)
            diff = subprocess.run(["git", "diff", "--cached", "--", ".", ":!hidden"], cwd=work, capture_output=True, text=True).stdout
            (out / f"{name}.patch").write_text(diff)
            rec = dict(task=t["id"], tier=t["tier"], backend=args.backend, model=model, effort=args.effort, rep=rep,
                       passed=passed, verify_tail=vout[-1500:], ts=time.strftime("%Y-%m-%dT%H:%M:%S"), **r)
            rec_path.write_text(json.dumps(rec, indent=1))
            print(f" {'PASS' if passed else 'FAIL'}  ${(r['cost_usd'] or 0):.3f}  {r['wall_s']:.0f}s  turns={r['turns']}"
                  + (f"  err={r['error'][:80]}" if r.get("error") else ""))
            if not keep_root:
                shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
