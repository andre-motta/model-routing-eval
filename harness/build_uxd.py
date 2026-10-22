#!/usr/bin/env python3
"""Build the tier 7 (skill pipeline) gallery: site/uxd/index.html.

For every run under eval/runs/model-routing-eval-uxd/ it copies the generated standalone prototype
(so it is browsable on GitHub Pages), screenshots every page x scenario with headless Chrome, and
writes one page with a run selector: judge score, cost, structural checks, and the screenshots
side by side with an "open live" link that lands on the same ?scenario=.

  python harness/build_uxd.py --out site/uxd            # after build_site.py (which recreates site/)
  python harness/build_uxd.py --out site/uxd --no-shots  # reuse screenshots already in the out dir
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_site import CSS, JS, esc, fmt_cost, PRETTY, TIER_OF  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "eval" / "runs" / "model-routing-eval-uxd"
RUNS_WS = ROOT / "eval" / "runs" / "model-routing-eval-uxdws"
CASE = "u01_uxd_prototype_create"
CASE_WS = "u02_uxd_prototype_workspace"
REPO_URL = "https://gitlab.cee.redhat.com/uxd/prototypes/rhoai"
ART = ".artifacts/RHAISTRAT-1527"
CHROME = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
RFE_URL = "https://redhat.atlassian.net/browse/RHAISTRAT-1527"
SKILL_URL = "https://github.com/rh-uxd/ai-helpers/tree/main/plugins/uxd-prototype/skills/uxd-prototype-create"


def model_key(model: str) -> str:
    m = model.rsplit("/", 1)[-1]  # rits/zai-org/glm-5-3 -> glm-5-3, rits/deepseek-ai/DeepSeek-... -> DeepSeek-...
    return m[len("claude-"):] if m.startswith("claude-") else m


def label(model: str, effort: str) -> str:
    return f"{PRETTY.get(model_key(model), model)} @ {effort}"


def tier_class(model: str) -> str:
    return TIER_OF.get(model_key(model), "floor")


def collect():
    runs = []
    for d in sorted(RUNS.iterdir()):
        rr = d / "run_result.json"
        case = d / "cases" / CASE
        if not rr.exists() or not (case / ART).is_dir():
            continue
        R = json.loads(rr.read_text())
        S = yaml.safe_load((d / "summary.yaml").read_text()) if (d / "summary.yaml").exists() else {}
        pc = (S.get("per_case") or {}).get(CASE, {})
        rc = (R.get("per_case") or {}).get(CASE, {})
        checks, failed = [], []
        vl = case / "output" / "verify.log"
        if vl.exists():
            for line in vl.read_text().splitlines():
                m = re.match(r"\[(PASS|FAIL|warn)\] (.*)", line)
                if m:
                    checks.append((m.group(1), m.group(2)))
                elif line.startswith("{"):
                    try:
                        failed = json.loads(line).get("failed_required", [])
                    except json.JSONDecodeError:
                        pass
        scen = {}
        sp = case / ART / "scenarios.json"
        if sp.exists():
            try:
                scen = json.loads(sp.read_text())
            except json.JSONDecodeError:
                scen = {}
        proto_dir = case / ART / "prototype"
        htmls = sorted(str(p.relative_to(proto_dir)) for p in proto_dir.rglob("*.html")
                       if "uxd-prototype-bar" not in p.parts and "decisions" not in p.parts) if proto_dir.is_dir() else []
        pages = []
        for pg in scen.get("pages") or []:
            route = str(pg.get("route") or "")
            html = None
            base = route.strip("/").split("?")[0]
            leaf = base.split("/")[-1]
            cands = ([base] if base.endswith(".html") else []) + [f"{base}.html", f"{base}/index.html", f"{leaf}.html", f"{leaf}/index.html"]
            if base in ("", "index"):
                cands.append("index.html")
            for cand in cands:
                if cand in htmls:
                    html = cand
                    break
            if html is None and len(htmls) == 1:
                html = htmls[0]
            if html is None and "index.html" in htmls and not any(p.get("html") == "index.html" for p in pages):
                html = "index.html"
            if html is None:
                continue
            ids = []
            for s in pg.get("scenarios") or []:
                sid = str(s.get("id") or "")
                if re.match(r"^[a-z0-9-]+$", sid):
                    ids.append((sid, str(s.get("name") or sid)))
            if not any(i == "default" for i, _ in ids):
                ids.insert(0, ("default", "Default"))
            pages.append({"route": route, "html": html, "screen": pg.get("screen") or html, "scenarios": ids})
        if not pages and htmls:
            pages = [{"route": "/", "html": h, "screen": h, "scenarios": [("default", "Default")]} for h in htmls]
        runs.append({
            "id": d.name, "model": R.get("model", ""), "effort": (R.get("eval_params") or {}).get("effort", ""),
            "agent": R.get("agent", ""), "cost": rc.get("cost_usd", R.get("cost_usd")), "wall": rc.get("duration_s") or R.get("duration_s"),
            "turns": rc.get("num_turns") or R.get("num_turns"),
            "passed": (pc.get("artifacts_complete") or {}).get("value"),
            "quality": (pc.get("prototype_quality") or {}).get("value"),
            "rationale": (pc.get("prototype_quality") or {}).get("rationale", ""),
            "checks": checks, "failed": failed, "pages": pages, "case_dir": case,
            "n_scenarios": sum(len(p["scenarios"]) - 1 for p in pages),
        })
    return runs


def collect_ws():
    """Workspace-mode runs: no HTML to screenshot; the deliverable is a diff against the rhoai codebase."""
    runs = []
    if not RUNS_WS.is_dir():
        return runs
    for d in sorted(RUNS_WS.iterdir()):
        rr = d / "run_result.json"
        case = d / "cases" / CASE_WS
        if not rr.exists() or not (case / "output").is_dir():
            continue
        R = json.loads(rr.read_text())
        S = yaml.safe_load((d / "summary.yaml").read_text()) if (d / "summary.yaml").exists() else {}
        pc = (S.get("per_case") or {}).get(CASE_WS, {})
        rc = (R.get("per_case") or {}).get(CASE_WS, {})
        checks, failed, changed, scen_ids = [], [], [], []
        vl = case / "output" / "verify.log"
        if vl.exists():
            for line in vl.read_text().splitlines():
                m = re.match(r"\[(PASS|FAIL|warn)\] (.*)", line)
                if m:
                    checks.append((m.group(1), m.group(2)))
                elif line.startswith("{"):
                    try:
                        j = json.loads(line)
                        failed, changed, scen_ids = j.get("failed_required", []), j.get("changed_src", []), j.get("non_default_scenarios", [])
                    except json.JSONDecodeError:
                        pass
        diff_p = case / "output" / "solution.diff"
        diff = diff_p.read_text(errors="replace") if diff_p.exists() else ""
        # keep the src/ part of the diff for the page; artifacts and bar assets are noise
        parts = re.split(r"(?m)^(?=diff --git )", diff)
        src_diff = "".join(p for p in parts if p.startswith("diff --git a/src/") and "uxd-prototype-bar" not in p.split("\n", 1)[0])
        runs.append({
            "id": d.name, "model": R.get("model", ""), "effort": (R.get("eval_params") or {}).get("effort", ""),
            "agent": R.get("agent", ""), "cost": rc.get("cost_usd", R.get("cost_usd")), "wall": rc.get("duration_s") or R.get("duration_s"),
            "turns": rc.get("num_turns") or R.get("num_turns"),
            "passed": (pc.get("artifacts_complete") or {}).get("value"),
            "quality": (pc.get("prototype_quality") or {}).get("value"),
            "rationale": (pc.get("prototype_quality") or {}).get("rationale", ""),
            "checks": checks, "failed": failed, "changed": changed, "scenarios": scen_ids,
            "diff_lines": sum(1 for l in src_diff.splitlines() if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))),
            "diff": src_diff[:200000],
        })
    return runs


def shoot(run, out: Path, jobs):
    dest = out / run["id"]
    (dest / "shots").mkdir(parents=True, exist_ok=True)
    proto = run["case_dir"] / ART / "prototype"
    if (dest / "prototype").exists():
        shutil.rmtree(dest / "prototype")
    shutil.copytree(proto, dest / "prototype")
    for f in ("scenarios.json", "journeys.json", "metadata.json", "prototype-summary.yaml", "changeset.md"):
        if (run["case_dir"] / ART / f).exists():
            shutil.copy(run["case_dir"] / ART / f, dest / f)
    for pg in run["pages"]:
        for sid, _ in pg["scenarios"]:
            png = dest / "shots" / f"{pg['html'].replace('/', '_').removesuffix('.html')}__{sid}.png"
            url = f"file://{(dest / 'prototype' / pg['html']).resolve()}?scenario={sid}"
            jobs.append((url, png))


CACHE = ROOT / ".cache" / "uxd-shots"


def chrome(url, png):
    """Screenshot url to png; cached under .cache/uxd-shots/<run>/<name> so a site rebuild (which wipes site/) is cheap."""
    cached = CACHE / png.parent.parent.name / png.name
    if not (cached.exists() and cached.stat().st_size > 0):
        cached.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="uxd-chrome-") as ud:
            cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", f"--user-data-dir={ud}",
                   "--window-size=1280,860", "--virtual-time-budget=8000", f"--screenshot={cached}", url]
            try:
                subprocess.run(cmd, capture_output=True, timeout=90)
            except subprocess.TimeoutExpired:
                pass
    if cached.exists():
        shutil.copy(cached, png)


def page(runs, out: Path):
    ws_html, ws_js = ws_section(collect_ws())
    order = sorted(runs, key=lambda r: ((r["cost"] or 0), r["id"]))
    def score(r):
        return "" if r["quality"] is None else f"{r['quality']}/5"
    rows = []
    for r in order:
        ok = r["passed"]
        pill = '<span class="pill ok">checks pass</span>' if ok else (f'<span class="pill bad">{len(r["failed"])} checks failed</span>' if ok is not None else "")
        rows.append(f"<tr data-run='{esc(r['id'])}'><td><button class='sel' data-run='{esc(r['id'])}'>{esc(label(r['model'], r['effort']))}</button></td>"
                    f"<td>{esc(r['agent'])}</td><td class='num'>{score(r)}</td><td>{pill}</td><td class='num'>{r['n_scenarios']}</td>"
                    f"<td class='num'>{'' if r['cost'] is None else fmt_cost(r['cost'])}</td><td class='num'>{'' if not r['wall'] else f'{r['wall']:.0f} s'}</td>"
                    f"<td class='num'>{r['turns'] or ''}</td></tr>")
    manifest = [{
        "id": r["id"], "label": label(r["model"], r["effort"]), "model": r["model"], "effort": r["effort"], "agent": r["agent"],
        "tier": tier_class(r["model"]), "cost": r["cost"], "wall": r["wall"], "turns": r["turns"], "passed": r["passed"],
        "quality": r["quality"], "rationale": r["rationale"], "checks": r["checks"], "failed": r["failed"],
        "pages": [{"screen": p["screen"], "html": p["html"], "scenarios": [{"id": i, "name": n, "shot": f"{r['id']}/shots/{p['html'].replace('/', '_').removesuffix('.html')}__{i}.png"} for i, n in p["scenarios"]]} for p in r["pages"]],
    } for r in order]
    extra_css = """
.pill.ok{background:#d8f1e4;color:#0b5b36} .pill.bad{background:#f8d9d2;color:#8a1f0a}
:root[data-theme="dark"] .pill.ok,:root:not([data-theme="light"]) .pill.ok{background:#17432e;color:#9fe2c1}
button.sel,button.selws{all:unset;cursor:pointer;color:var(--floor);text-decoration:underline} button.sel.on,button.selws.on{font-weight:700;color:var(--ink)}
.tabs{display:flex;flex-wrap:wrap;gap:.3rem;margin:.6rem 0} .tabs button{border:1px solid var(--grid);background:var(--surface-2);color:var(--ink);border-radius:4px;padding:.25rem .6rem;cursor:pointer;font:inherit;font-size:.85rem}
.tabs button.on{background:var(--ink);color:var(--surface);border-color:var(--ink)}
body{max-width:1500px}
.shot{border:1px solid var(--grid);border-radius:4px;max-width:100%;display:block;background:#fff}
.frame{width:100%;height:860px;border:1px solid var(--grid);border-radius:4px;background:#fff;display:block}
.viewtabs{display:flex;gap:.3rem;margin:.6rem 0 .3rem} .viewtabs button{border:1px solid var(--grid);background:var(--surface-2);color:var(--ink);border-radius:4px;padding:.25rem .6rem;cursor:pointer;font:inherit;font-size:.85rem} .viewtabs button.on{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.hdr{display:flex;flex-wrap:wrap;gap:.6rem 1.4rem;align-items:baseline;margin:.6rem 0}
.hdr .big{font-family:'Red Hat Display',system-ui,sans-serif;font-size:1.6rem;font-weight:600}
.checks{columns:2;column-gap:1.5rem;font-size:.85rem} .checks li{break-inside:avoid;list-style:none;padding-left:1.2rem;text-indent:-1.2rem} .checks li::before{content:"✓ ";color:#0b8a4a} .checks li.f::before{content:"✗ ";color:#c21807}
@media (max-width:640px){.checks{columns:1}}
"""
    js = """
const M=%s; const byId=Object.fromEntries(M.map(r=>[r.id,r])); let cur=null, page=0, sc=0, view='live';
document.getElementById('v-live').onclick=()=>{view='live';render();}; document.getElementById('v-shot').onclick=()=>{view='shot';render();};
function pick(id){cur=byId[id]; page=0; sc=0; location.hash=id; render();}
function render(){const r=cur; document.querySelectorAll('button.sel').forEach(b=>b.classList.toggle('on',b.dataset.run===r.id));
  const h=document.getElementById('hdr'); h.innerHTML='';
  const add=(v,l)=>{const d=document.createElement('div'); const b=document.createElement('div'); b.className='big'; b.textContent=v; const s=document.createElement('div'); s.className='note'; s.textContent=l; d.append(b,s); h.appendChild(d);};
  add(r.label, r.agent); add(r.quality==null?'n/a':r.quality+' / 5','Opus 5.5 judge: MVP coverage'); add(r.passed?'pass':(r.passed==null?'n/a':'fail'),'structural checks ('+r.checks.length+')');
  add(r.cost==null?'n/a':'$'+r.cost.toFixed(2),'cost, list price'); add(r.wall?Math.round(r.wall)+' s':'n/a','wall time'); add(r.turns||'n/a','agent turns');
  document.getElementById('rat').textContent=r.rationale||'(not judged yet)';
  const ul=document.getElementById('checks'); ul.innerHTML=''; r.checks.forEach(([f,t])=>{const li=document.createElement('li'); if(f==='FAIL') li.className='f'; li.textContent=t; ul.appendChild(li);});
  const pt=document.getElementById('pages'); pt.innerHTML=''; r.pages.forEach((p,i)=>{const b=document.createElement('button'); b.textContent=p.screen; b.classList.toggle('on',i===page); b.onclick=()=>{page=i;sc=0;render();}; pt.appendChild(b);});
  const st=document.getElementById('scen'); st.innerHTML=''; const P=r.pages[page]; if(!P){document.getElementById('shot').removeAttribute('src'); return;}
  P.scenarios.forEach((s,i)=>{const b=document.createElement('button'); b.textContent=s.id; b.title=s.name; b.classList.toggle('on',i===sc); b.onclick=()=>{sc=i;render();}; st.appendChild(b);});
  const S=P.scenarios[sc]; const img=document.getElementById('shot'); img.src=S.shot; img.alt=r.label+' '+P.screen+' '+S.id;
  const url=r.id+'/prototype/'+P.html+'?scenario='+S.id; const fr=document.getElementById('frame'); if(view==='live'){fr.src=url;} else {fr.removeAttribute('src');}
  fr.hidden=view!=='live'; img.hidden=view!=='shot'; document.getElementById('v-live').classList.toggle('on',view==='live'); document.getElementById('v-shot').classList.toggle('on',view==='shot');
  const live=document.getElementById('live'); live.href=url; live.textContent='Open the live prototype in a new tab at ?scenario='+S.id;
  document.getElementById('cap').textContent=P.screen+' / '+S.name;}
document.querySelectorAll('button.sel').forEach(b=>b.onclick=()=>pick(b.dataset.run));
const first=(location.hash||'').slice(1); pick(byId[first]?first:(M.find(r=>r.quality!=null)||M[0]).id);
""" % json.dumps(manifest).replace("</", "<\\/")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Skill pipeline results</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}{extra_css}</style></head><body>
<p class="note"><a href="../">← All results</a></p>
<h1>Tier 7: one team skill, every model</h1><div class="rule"></div>
<p class="lede">The UXD team's <a href="{SKILL_URL}">uxd-prototype-create</a> skill run headlessly, once per model and effort, on
<a href="{RFE_URL}">RHAISTRAT-1527</a> (Multimodal Support in Gen AI Studio Playground), standalone mode, decisions skipped.
Every run got the same RFE snapshot and the same instruction to proceed without confirmation. A structural checker verifies the artifacts the skill
promises; Claude Opus 5.5 scores how well the prototype covers the RFE's MVP scope (1 to 5). Pick a run to see what it built.
Prototypes that render in a narrow column (GLM 5.3, Haiku 5.5) are shown as generated: they placed the nav and main content straight into
<code>pf-v6-c-page</code> without the sidebar and main classes, so the PatternFly grid stacks everything in its first column. The judge reads the
HTML, not the render, and did not catch that.</p>
<h2>Runs</h2>
<table><thead><tr><th>model @ effort</th><th>agent</th><th class="num">judge</th><th>checks</th><th class="num">scenarios</th><th class="num">cost</th><th class="num">wall</th><th class="num">turns</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p class="note">Cost is list price from token usage; EnMaaS runs are free. GLM 5.3 ran at max reasoning. Scenarios counts the non-default <code>?scenario=</code> states the run declared in scenarios.json.</p>
<h2>What it built</h2>
<div class="hdr" id="hdr"></div>
<p><b>Judge:</b> <span id="rat"></span></p>
<details><summary>Structural checks</summary><ul class="checks" id="checks"></ul></details>
<div class="tabs" id="pages"></div>
<div class="tabs" id="scen"></div>
<div class="viewtabs"><button id="v-live" class="on">Live prototype</button><button id="v-shot">Screenshot (1280 px)</button></div>
<figure><iframe class="frame" id="frame" title="live prototype" loading="lazy"></iframe><img class="shot" id="shot" alt="" hidden><figcaption id="cap"></figcaption><p class="note"><a id="live" href="#" target="_blank" rel="noopener">Open the live prototype in a new tab</a> (PatternFly from CDN; the Prototype Bar on top is the skill's own; the iframe is the real page, so resize the window to see how it reflows).</p></figure>
{ws_html}
<p class="note">Built by <code>harness/build_uxd.py</code>. Screenshots are headless Chrome at 1280 px.</p>
<script>{JS}</script><script>{js}</script>{ws_js}</body></html>"""
    (out / "index.html").write_text(html)
    # Old prototype URLs of runs renamed after publication (GLM ran at max, not medium)
    for old_id, new_id in {"2026-10-19-glm-5-3-effort-medium": "2026-10-19-glm-5-3-effort-max",
                           "2026-10-19-glm-5-3-effort-medium-r1": "2026-10-19-glm-5-3-effort-max-r1"}.items():
        d = out / old_id; d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../{new_id}/">'
                                      f'<title>Moved</title></head><body><p>Moved to <a href="../{new_id}/">{new_id}</a>.</p></body></html>')


def ws_section(runs_ws):
    if not runs_ws:
        return "", ""
    order = sorted(runs_ws, key=lambda r: ((r["cost"] or 0), r["id"]))
    rows = []
    for r in order:
        ok = r["passed"]
        pill = '<span class="pill ok">checks pass</span>' if ok else (f'<span class="pill bad">{len(r["failed"])} checks failed</span>' if ok is not None else "")
        rows.append(f"<tr><td><button class='selws' data-run='{esc(r['id'])}'>{esc(label(r['model'], r['effort']))}</button></td>"
                    f"<td>{esc(r['agent'])}</td><td class='num'>{'' if r['quality'] is None else str(r['quality']) + '/5'}</td><td>{pill}</td>"
                    f"<td class='num'>{len(r['scenarios'])}</td><td class='num'>{len(r['changed'])}</td><td class='num'>{r['diff_lines']}</td>"
                    f"<td class='num'>{'' if r['cost'] is None else fmt_cost(r['cost'])}</td><td class='num'>{'' if not r['wall'] else f'{r['wall']:.0f} s'}</td></tr>")
    manifest = [{"id": r["id"], "label": label(r["model"], r["effort"]), "agent": r["agent"], "cost": r["cost"], "wall": r["wall"], "turns": r["turns"],
                 "passed": r["passed"], "quality": r["quality"], "rationale": r["rationale"], "checks": r["checks"], "changed": r["changed"],
                 "scenarios": r["scenarios"], "diff": r["diff"]} for r in order]
    html = f"""
<h2 id="workspace">Workspace mode: the same skill inside the team's codebase</h2>
<p class="lede">Second variant, requested by the skill's author: <code>--workspace .</code> on <a href="{REPO_URL}">uxd/prototypes/rhoai</a>
(branch 3.6, pinned), the UXD team's React and PatternFly 6 prototype app that already has a Gen AI Studio Playground. The agent must extend the
codebase following its conventions, register routes, wire <code>?scenario=</code> through <code>useUxdScenario</code>, and leave type-check and lint
passing. The checker runs <code>tsc</code> and eslint on the changed files (no new errors against the repo's baseline). No screenshots here: the
deliverable is the diff.</p>
<table><thead><tr><th>model @ effort</th><th>agent</th><th class="num">judge</th><th>checks</th><th class="num">scenarios</th><th class="num">files</th><th class="num">diff lines</th><th class="num">cost</th><th class="num">wall</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<div class="hdr" id="wshdr"></div>
<p><b>Judge:</b> <span id="wsrat"></span></p>
<details><summary>Structural checks</summary><ul class="checks" id="wschecks"></ul></details>
<details><summary>Changed files under src/</summary><ul id="wsfiles" class="checks"></ul></details>
<details open><summary>Diff against the pinned codebase (src/ only)</summary><pre id="wsdiff" style="white-space:pre-wrap;font-size:.78rem;max-height:600px;overflow:auto;background:var(--surface-2);padding:.6rem;border-radius:4px"></pre></details>
"""
    js = """<script>
const W=%s; const wById=Object.fromEntries(W.map(r=>[r.id,r]));
function pickWs(id){const r=wById[id]; document.querySelectorAll('button.selws').forEach(b=>b.classList.toggle('on',b.dataset.run===id));
  const h=document.getElementById('wshdr'); h.innerHTML='';
  const add=(v,l)=>{const d=document.createElement('div'); const b=document.createElement('div'); b.className='big'; b.textContent=v; const s=document.createElement('div'); s.className='note'; s.textContent=l; d.append(b,s); h.appendChild(d);};
  add(r.label, r.agent); add(r.quality==null?'n/a':r.quality+' / 5','Opus 5.5 judge'); add(r.passed?'pass':(r.passed==null?'n/a':'fail'),'checks ('+r.checks.length+')');
  add(r.cost==null?'n/a':'$'+r.cost.toFixed(2),'cost'); add(r.wall?Math.round(r.wall)+' s':'n/a','wall time'); add(r.changed.length,'files in src/');
  document.getElementById('wsrat').textContent=r.rationale||'(not judged yet)';
  const ul=document.getElementById('wschecks'); ul.innerHTML=''; r.checks.forEach(([f,t])=>{const li=document.createElement('li'); if(f==='FAIL') li.className='f'; li.textContent=t; ul.appendChild(li);});
  const fl=document.getElementById('wsfiles'); fl.innerHTML=''; r.changed.forEach(f=>{const li=document.createElement('li'); li.textContent=f; fl.appendChild(li);});
  document.getElementById('wsdiff').textContent=r.diff||'(no src/ changes)';}
document.querySelectorAll('button.selws').forEach(b=>b.onclick=()=>pickWs(b.dataset.run));
if(W.length) pickWs((W.find(r=>r.quality!=null)||W[0]).id);
</script>""" % json.dumps(manifest).replace("</", "<\\/")
    return html, js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site" / "uxd"))
    ap.add_argument("--no-shots", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = collect()
    if not runs:
        sys.exit("no uxd runs with artifacts under " + str(RUNS))
    jobs = []
    for r in runs:
        shoot(r, out, jobs)
    if not args.no_shots:
        if not CHROME:
            sys.exit("no google-chrome or chromium on PATH for screenshots (use --no-shots)")
        with ThreadPoolExecutor(args.workers) as ex:
            list(ex.map(lambda j: chrome(*j), jobs))
    page(runs, out)
    print(f"wrote {out}/index.html: {len(runs)} standalone runs, {len(collect_ws())} workspace runs, {len(jobs)} screenshots")


if __name__ == "__main__":
    main()
