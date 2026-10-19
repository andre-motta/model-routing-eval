#!/usr/bin/env python3
"""Structural verifier for a uxd-prototype-create run (standalone mode).

Usage: python3 check_prototype.py <artifacts-dir>

Checks that the skill produced every artifact its contract promises and that the
?scenario= wiring is present in the generated prototype. Prints one line per check
and a JSON summary; exit status 0 when every required check passes. The LLM judge
reads this log alongside the artifacts, so failures are described, not just counted.
"""
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"^[a-z0-9-]+$")
REQUIRED_FILES = ["journeys.json", "scenarios.json", "metadata.json", "changeset.md", "prototype-summary.yaml"]


def load_json(p: Path):
    try:
        return json.loads(p.read_text()), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"


def main(root: str) -> int:
    art = Path(root)
    checks = []  # (name, ok, detail, required)

    def add(name, ok, detail="", required=True):
        checks.append({"check": name, "ok": bool(ok), "detail": detail, "required": required})

    # 1. Required artifact files
    for f in REQUIRED_FILES:
        p = art / f
        add(f"file:{f}", p.is_file() and p.stat().st_size > 0, "" if p.is_file() else "missing or empty")

    # 2. journeys.json
    journeys, err = load_json(art / "journeys.json")
    routes = set()
    if journeys is None:
        add("journeys:valid", False, err)
    else:
        js = journeys.get("journeys") or []
        steps = [s for j in js for s in (j.get("steps") or [])]
        routes = {s.get("route") for s in steps if s.get("route")}
        add("journeys:valid", bool(js) and bool(steps), f"{len(js)} journeys, {len(steps)} steps, {len(routes)} routes")
        add("journeys:ids", all(ID_RE.match(str(s.get("id", ""))) for s in steps), "step ids must be [a-z0-9-]+", required=False)

    # 3. scenarios.json
    scen, err = load_json(art / "scenarios.json")
    non_default_ids = []
    if scen is None:
        add("scenarios:valid", False, err)
    else:
        pages = scen.get("pages") or []
        ok_default = True
        page_routes = set()
        for pg in pages:
            page_routes.add(pg.get("route"))
            ss = pg.get("scenarios") or []
            defaults = [s for s in ss if s.get("default") or s.get("id") == "default"]
            ok_default &= len(defaults) >= 1
            for s in ss:
                sid = str(s.get("id", ""))
                if sid != "default" and not s.get("default"):
                    non_default_ids.append(sid)
        add("scenarios:valid", bool(pages), f"{len(pages)} pages, {len(non_default_ids)} non-default scenarios")
        add("scenarios:default-per-page", ok_default, "every page needs a default scenario")
        add("scenarios:ids", all(ID_RE.match(s) for s in non_default_ids), "scenario ids must be [a-z0-9-]+")
        add("scenarios:at-least-3-variants", len(non_default_ids) >= 3,
            "the RFE's MVP scope supports at least three non-default end states (unsupported modality, large file, audio)")
        missing = sorted(r for r in routes if r not in page_routes)
        add("scenarios:cover-journey-routes", not missing, f"journey routes without a scenarios page: {missing}" if missing else "")

    # 4. metadata.json
    meta, err = load_json(art / "metadata.json")
    if meta is None:
        add("metadata:valid", False, err)
    else:
        add("metadata:valid", meta.get("prototype_id") == "RHAISTRAT-1527", f"prototype_id={meta.get('prototype_id')}")
        add("metadata:decision-mode-skip", meta.get("decision_mode") == "skip", f"decision_mode={meta.get('decision_mode')}", required=False)

    # 5. prototype-summary.yaml (yaml may be unavailable in the workspace venv; fall back to a text check)
    ps = art / "prototype-summary.yaml"
    if ps.is_file():
        try:
            import yaml  # type: ignore
            d = yaml.safe_load(ps.read_text())
            add("summary:valid", isinstance(d, dict) and "prototype_summary" in d, "needs a prototype_summary root key")
        except ImportError:
            add("summary:valid", "prototype_summary" in ps.read_text(), "needs a prototype_summary root key")
        except Exception as e:  # noqa: BLE001
            add("summary:valid", False, f"invalid YAML: {e}")

    # 6. prototype HTML
    proto = art / "prototype"
    htmls = [p for p in proto.rglob("*.html")] if proto.is_dir() else []
    htmls = [p for p in htmls if "uxd-prototype-bar" not in p.parts and "decisions" not in p.parts]
    add("prototype:html", bool(htmls), f"{len(htmls)} html files" if htmls else "no html under prototype/")
    text = "\n".join(p.read_text(errors="replace") for p in htmls)
    js_text = "\n".join(p.read_text(errors="replace") for p in proto.rglob("*.js")
                        if "uxd-prototype-bar" not in p.parts) if proto.is_dir() else ""
    add("prototype:patternfly6", bool(re.search(r"@patternfly/patternfly@6", text)), "PatternFly 6 CDN stylesheet link")
    wired = bool(re.search(r"UxdScenario|URLSearchParams\([^)]*\)\.get\(\s*['\"]scenario['\"]|[?&]scenario=", text + js_text))
    add("prototype:scenario-wiring", wired, "reads ?scenario= (UxdScenario.get() or URLSearchParams)")
    present = [s for s in non_default_ids if s in text + js_text]
    absent = [s for s in non_default_ids if s not in text + js_text]
    add("prototype:scenario-ids-in-code", bool(non_default_ids) and not absent,
        f"scenario ids not referenced by the prototype code: {absent}" if absent else f"{len(present)} ids wired")

    # 7. Prototype Bar
    bar_cfg = art / "prototype-bar.json"
    bar_assets = proto.is_dir() and any(p.name.startswith("prototype-bar") or p.name == "uxd-scenario-runtime.js" for p in proto.rglob("*"))
    bar_ref = bool(re.search(r"prototype-bar-standalone\.js|uxd-scenario-runtime\.js|uxd-prototype-bar", text))
    add("bar:config", bar_cfg.is_file(), "prototype-bar.json written")
    add("bar:installed", bar_assets and bar_ref, "bar assets copied into prototype/ and referenced from the HTML")

    # 8. Nothing written outside the artifacts tree is checked by the diff; here only forbid artifacts under the plugin.
    required_fail = [c for c in checks if c["required"] and not c["ok"]]
    for c in checks:
        flag = "PASS" if c["ok"] else ("FAIL" if c["required"] else "warn")
        print(f"[{flag}] {c['check']}" + (f": {c['detail']}" if c["detail"] else ""))
    summary = {"passed": not required_fail, "checks": len(checks), "failed_required": [c["check"] for c in required_fail],
               "non_default_scenarios": non_default_ids, "html_files": [str(p.relative_to(art)) for p in htmls]}
    print(json.dumps(summary))
    return 0 if not required_fail else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ".artifacts/RHAISTRAT-1527"))
