#!/usr/bin/env python3
"""Structural verifier for a uxd-prototype-create run in workspace mode (React codebase).

Usage: python3 check_workspace.py <artifacts-dir>      (run from the workspace root)

Checks the artifacts the skill promises for workspace mode, that the prototype landed in src/
wired to ?scenario=, and that the codebase still type-checks and lints (the skill's own Step 11
contract). Prints one line per check and a JSON summary; exit 0 when every required check passes.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9-]+$")
REQUIRED_FILES = ["journeys.json", "scenarios.json", "metadata.json", "changeset.md", "prototype-summary.yaml", "workspace-analysis.json"]


def load_json(p: Path):
    try:
        return json.loads(p.read_text()), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def run(cmd, timeout=900):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"


def main(root: str) -> int:
    art = Path(root)
    checks = []

    def add(name, ok, detail="", required=True):
        checks.append({"check": name, "ok": bool(ok), "detail": detail or "", "required": required})

    for f in REQUIRED_FILES:
        p = art / f
        add(f"file:{f}", p.is_file() and p.stat().st_size > 0, "" if p.is_file() else "missing or empty")
    add("file:verification.json", (art / "verification.json").is_file(), "Step 11 record", required=False)

    journeys, err = load_json(art / "journeys.json")
    routes = set()
    if journeys is None:
        add("journeys:valid", False, err or "")
    else:
        js = journeys.get("journeys") or []
        steps = [s for j in js for s in (j.get("steps") or [])]
        routes = {s.get("route") for s in steps if s.get("route")}
        add("journeys:valid", bool(js) and bool(steps), f"{len(js)} journeys, {len(steps)} steps, {len(routes)} routes")

    scen, err = load_json(art / "scenarios.json")
    non_default = []
    if scen is None:
        add("scenarios:valid", False, err or "")
    else:
        pages = scen.get("pages") or []
        ok_default = True
        page_routes = set()
        for pg in pages:
            page_routes.add(pg.get("route"))
            ss = pg.get("scenarios") or []
            ok_default &= any(s.get("default") or s.get("id") == "default" for s in ss)
            non_default += [str(s.get("id", "")) for s in ss if s.get("id") != "default" and not s.get("default")]
        add("scenarios:valid", bool(pages), f"{len(pages)} pages, {len(non_default)} non-default scenarios")
        add("scenarios:default-per-page", ok_default, "every page needs a default scenario")
        add("scenarios:ids", all(ID_RE.match(s) for s in non_default), "scenario ids must be [a-z0-9-]+")
        add("scenarios:at-least-3-variants", len(non_default) >= 3, "unsupported modality, large file, audio at minimum")
        missing = sorted(r for r in routes if r not in page_routes)
        add("scenarios:cover-journey-routes", not missing, f"journey routes without a scenarios page: {missing}" if missing else "")

    meta, err = load_json(art / "metadata.json")
    if meta is None:
        add("metadata:valid", False, err or "")
    else:
        add("metadata:valid", meta.get("prototype_id") == "RHAISTRAT-1527", f"prototype_id={meta.get('prototype_id')}")
        add("metadata:build-mode", meta.get("build_mode") == "existing-codebase", f"build_mode={meta.get('build_mode')}", required=False)

    wa, err = load_json(art / "workspace-analysis.json")
    if wa is None:
        add("workspace-analysis:valid", False, err or "")
    else:
        add("workspace-analysis:valid", bool(wa.get("tech_stack")) and bool(wa.get("workspace_path") or wa.get("rfe_key")),
            f"framework={((wa.get('tech_stack') or {}).get('framework'))}")

    # Code changes in src/ (the workspace root is the cwd; node_modules and dist are excluded by .git/info/exclude)
    rc, out = run("git status --porcelain -- src")
    changed = [l[3:].strip() for l in out.splitlines() if l.strip()]
    src_files = [f for f in changed if f.startswith("src/") and f.endswith((".ts", ".tsx"))]
    add("code:changes-in-src", bool(src_files), f"{len(src_files)} ts/tsx files changed under src/" if src_files else "no ts/tsx changes under src/")
    code = ""
    for f in src_files:
        try:
            code += Path(f).read_text(errors="replace") + "\n"
        except OSError:
            pass
    add("code:scenario-wiring", bool(re.search(r"UxdScenario|useUxdScenario", code)), "reads the active scenario via window.UxdScenario / useUxdScenario")
    absent = [s for s in non_default if s not in code]
    add("code:scenario-ids-in-code", bool(non_default) and not absent, f"ids not referenced in changed src files: {absent}" if absent else f"{len(non_default)} ids wired")
    rc, out = run("git status --porcelain -- src/app/routes.tsx src/app/AppLayout")
    add("code:route-or-nav-registered", bool(out.strip()), "routes.tsx or AppLayout changed (new screens reachable)", required=False)
    bar = Path("src/components/uxd-prototype-bar").is_dir() or "PrototypeBar" in code
    add("bar:installed", bar, "Prototype Bar component copied into src/components or imported", required=False)

    # Step 11: type-check and lint on the changed files
    rc, out = run("npm run -s type-check", timeout=1200)
    add("verify:type-check", rc == 0, "" if rc == 0 else out.strip().splitlines()[-1][:300] if out.strip() else f"exit {rc}")
    if src_files:
        # The repo already carries lint errors; require that the changed files add none. Baseline = eslint on the
        # HEAD version of each pre-existing changed file (written next to it so the same config applies).
        def errors(files):
            if not files:
                return 0, ""
            p = subprocess.run("npx eslint -f json --ext .tsx,.ts " + " ".join(f"'{f}'" for f in files), shell=True,
                               capture_output=True, text=True, timeout=900)
            try:
                rep = json.loads(p.stdout)
                return sum(r.get("errorCount", 0) for r in rep), ""
            except json.JSONDecodeError:
                return -1, (p.stderr or p.stdout)[-300:]
        base_files = []
        for f in src_files:
            show = subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, text=True)
            if show.returncode == 0:
                bf = f.rsplit(".", 1)[0] + ".__lintbase." + f.rsplit(".", 1)[1]
                Path(bf).write_text(show.stdout)
                base_files.append(bf)
        base_n, base_err = errors(base_files)
        for bf in base_files:
            Path(bf).unlink(missing_ok=True)
        new_n, new_err = errors(src_files)
        ok = new_n >= 0 and base_n >= 0 and new_n <= base_n
        add("verify:lint-no-new-errors", ok, f"eslint errors in changed files: {new_n} (baseline {base_n})" if not (new_err or base_err) else (new_err or base_err))

    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    for c in checks:
        flag = "PASS" if c["ok"] else ("FAIL" if c["required"] else "warn")
        print(f"[{flag}] {c['check']}" + (f": {c['detail']}" if c["detail"] else ""))
    print(json.dumps({"passed": not required_fail, "checks": len(checks), "failed_required": [c["check"] for c in required_fail],
                      "non_default_scenarios": non_default, "changed_src": src_files}))
    return 0 if not required_fail else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ".artifacts/RHAISTRAT-1527"))
