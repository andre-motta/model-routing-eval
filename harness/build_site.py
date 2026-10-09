#!/usr/bin/env python3
"""Build the static results site (GitHub Pages): index with native SVG charts and tables, the
eval-anova compare report(s), and every per-run harness report.

  python harness/build_site.py --out site
"""
import argparse
import html
import json
import math
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import ROOT  # noqa: E402

RUNS = ROOT / "eval" / "runs" / "model-routing-eval"
ANOVA = ROOT / "eval" / "anova"
RESULTS = ROOT / "results" / "harness"

TIER_NAMES = {1: "Mechanical", 2: "Bounded impl.", 3: "Debugging", 4: "Architecture", 5: "Long context", 6: "Real repo"}
PRETTY = {"glm-5-3": "GLM 5.3", "gpt-6-luna": "Luna", "gpt-6.1-sol": "Sol 6.1", "gpt-5.6-terra": "Terra 5.6",
          "gpt-6-astra": "Astra", "haiku-5-5": "Haiku 5.5", "sonnet-5-5": "Sonnet 5.5", "opus-5-5": "Opus 5.5", "fable-5-1": "Fable 5.1"}
# Price tier of each model. Colour follows the tier (an entity attribute), never the rank.
TIER_OF = {"glm-5-3": "free", "gpt-6-luna": "floor", "haiku-5-5": "floor", "gpt-6.1-sol": "middle", "sonnet-5-5": "middle",
           "gpt-5.6-terra": "middle", "opus-5-5": "flagship", "gpt-6-astra": "flagship", "fable-5-1": "flagship"}
TIER_LABEL = {"floor": "Floor tier ($0.10 per 1M input)", "middle": "Middle tier ($2)", "flagship": "Flagship tier ($4 to $10)", "free": "Free (GLM via EnMaaS)"}

CSS = """
:root{color-scheme:light;--surface:#fcfcfb;--surface-2:#f0efec;--grid:#e3e2de;--ink:#0b0b0b;--ink-2:#52514e;--ink-3:#8a8984;
 --floor:#2a78d6;--middle:#eb6834;--flagship:#1baf7a;--free:#8a8984;--accent:#e00;--seq-1:#cde2fb;--seq-2:#86b6ef;--seq-3:#3987e5;--seq-4:#1c5cab}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){color-scheme:dark;--surface:#1a1a19;--surface-2:#2a2a28;--grid:#383835;--ink:#fff;--ink-2:#c3c2b7;--ink-3:#8f8e88;
 --floor:#3987e5;--middle:#d95926;--flagship:#199e70;--free:#a3a29c;--seq-1:#184f95;--seq-2:#256abf;--seq-3:#5598e7;--seq-4:#9ec5f4}}
:root[data-theme="dark"]{color-scheme:dark;--surface:#1a1a19;--surface-2:#2a2a28;--grid:#383835;--ink:#fff;--ink-2:#c3c2b7;--ink-3:#8f8e88;
 --floor:#3987e5;--middle:#d95926;--flagship:#199e70;--free:#a3a29c;--seq-1:#184f95;--seq-2:#256abf;--seq-3:#5598e7;--seq-4:#9ec5f4}
*{box-sizing:border-box}
body{font-family:'Red Hat Text',system-ui,sans-serif;max-width:1120px;margin:0 auto;padding:1.5rem 16px 4rem;background:var(--surface);color:var(--ink);line-height:1.45}
h1,h2,h3{font-family:'Red Hat Display',system-ui,sans-serif;font-weight:600;letter-spacing:-.01em}
h1{font-size:2rem;margin:.2rem 0 .4rem} h2{font-size:1.35rem;margin:2.4rem 0 .4rem;padding-top:1.2rem;border-top:1px solid var(--grid)} h3{font-size:1.05rem;margin:1.2rem 0 .3rem}
p{margin:.4rem 0} .lede{font-size:1.05rem;color:var(--ink-2)} .note{color:var(--ink-3);font-size:.88rem} a{color:var(--floor)}
.rule{height:3px;background:var(--accent);width:72px;margin:.6rem 0 1rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin:1rem 0}
.tile{border:1px solid var(--grid);border-radius:6px;padding:.7rem .8rem;background:var(--surface)}
.tile .v{font-family:'Red Hat Display',system-ui,sans-serif;font-size:1.9rem;font-weight:600;line-height:1.1} .tile .l{color:var(--ink-2);font-size:.85rem;margin-top:.2rem}
figure{margin:1rem 0;padding:.9rem .9rem .6rem;border:1px solid var(--grid);border-radius:6px;background:var(--surface)}
figcaption{font-weight:600;margin-bottom:.1rem} figure .sub{color:var(--ink-2);font-size:.88rem;margin-bottom:.6rem}
svg{width:100%;height:auto;display:block;font-family:'Red Hat Text',system-ui,sans-serif}
.legend{display:flex;flex-wrap:wrap;gap:.3rem 1.1rem;font-size:.85rem;color:var(--ink-2);margin:.4rem 0 .2rem}
.legend span::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:.4rem;vertical-align:-1px;background:var(--c)}
table{border-collapse:collapse;width:100%;margin:.6rem 0;font-size:.9rem} th,td{border-bottom:1px solid var(--grid);padding:.35rem .55rem;text-align:left;vertical-align:top}
th{color:var(--ink-2);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600} td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.swatch{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:.45rem;vertical-align:0}
.pill{display:inline-block;font-size:.72rem;padding:.05rem .4rem;border-radius:3px;background:var(--surface-2);color:var(--ink-2);margin-left:.3rem}
details{margin:.6rem 0} summary{cursor:pointer;color:var(--ink-2)}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--surface);padding:.4rem .6rem;border-radius:4px;font-size:.82rem;line-height:1.35;max-width:300px;opacity:0;transition:opacity .08s;z-index:9}
.tip b{font-size:.95rem;display:block} .hit{fill:transparent;cursor:default} .mark:hover,.hit:hover+.mark{filter:brightness(1.12)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.6rem} .card{border:1px solid var(--grid);border-top:4px solid var(--accent);border-radius:4px;padding:.7rem .8rem;background:var(--surface)}
code{background:var(--surface-2);padding:.1rem .3rem;border-radius:3px;font-size:.9em}
@media (max-width:640px){h1{font-size:1.5rem} .tile .v{font-size:1.5rem}}
"""

JS = """
(function(){
  const tip=document.createElement('div');tip.className='tip';document.body.appendChild(tip);
  function show(e,el){const v=el.getAttribute('data-v'),l=el.getAttribute('data-l');tip.textContent='';
    const b=document.createElement('b');b.textContent=v;tip.appendChild(b);tip.appendChild(document.createTextNode(l));
    tip.style.opacity=1;move(e);}
  function move(e){const x=e.clientX+14,y=e.clientY+14;tip.style.left=Math.min(x,window.innerWidth-320)+'px';tip.style.top=Math.min(y,window.innerHeight-120)+'px';}
  function hide(){tip.style.opacity=0;}
  document.querySelectorAll('[data-v]').forEach(el=>{el.addEventListener('pointerenter',e=>show(e,el));el.addEventListener('pointermove',move);
    el.addEventListener('pointerleave',hide);el.addEventListener('focus',()=>{const r=el.getBoundingClientRect();show({clientX:r.left+r.width/2,clientY:r.top},el)});el.addEventListener('blur',hide);el.setAttribute('tabindex','0');});
})();
"""


SUFFIX = {}  # config -> " (hard subset)" or " (partial)"; filled in main()
HARD = {"r01_fromager_distinfo", "r02_fromager_age_filter", "r03_fromager_dep_chain", "r04_fromager_age_fallback",
        "r05_fromager_version_prebuilt", "t14_dep_resolver", "t15_perf_regression", "t16_json_patch"}


def pretty(cfg):
    m, _, e = cfg.partition("@")
    return f"{PRETTY.get(m, m)} {e}".strip() + SUFFIX.get(cfg, "")


def tier(cfg):
    return TIER_OF.get(cfg.partition("@")[0], "floor")


def esc(x):
    return html.escape(str(x))


def fmt_cost(c):
    return "$0" if c == 0 else (f"${c:.3f}" if c < 0.1 else f"${c:.2f}")


def load():
    S = json.loads((RESULTS / "report" / "summary.json").read_text())
    runs = S["per_run"]
    spec = [r for r in runs if not r["task"].endswith("_ticket")]
    tickets = [r for r in runs if r["task"].endswith("_ticket") and isinstance(r.get("quality"), (int, float)) and r["quality"] == r["quality"]]
    by = defaultdict(lambda: dict(n=0, p=0, cost=0.0, wall=0.0, reps=set(), tasks=set()))
    for r in spec:
        a = by[r["config"]]
        a["n"] += 1
        a["p"] += int(r["passed"])
        a["cost"] += r["cost"]
        a["wall"] += r["wall"]
        a["reps"].add(r["rep"])
        a["tasks"].add(r["task"])
    return S, runs, spec, tickets, by


# ----------------------------------------------------------------------------- charts (inline SVG)
def dot_chart(by, cfgs):
    """Pass rate (y) vs cost per case (x, log). One dot per configuration, direct labels, tier colour."""
    W, H, L, R, T, B = 980, 420, 56, 24, 20, 56
    pw, ph = W - L - R, H - T - B
    xmin, xmax = math.log10(0.0015), math.log10(2.0)
    ymin, ymax = 0.72, 1.005

    def X(c):
        return L + (math.log10(max(c, 0.002)) - xmin) / (xmax - xmin) * pw

    def Y(p):
        return T + (ymax - p) / (ymax - ymin) * ph
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Pass rate versus cost per case, one dot per configuration">']
    for p in (0.75, 0.80, 0.85, 0.90, 0.95, 1.0):
        y = Y(p)
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--grid)" stroke-width="1"/>'
                   f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end" font-size="12" fill="var(--ink-2)">{p:.0%}</text>')
    for c, lab in ((0.002, "$0.002"), (0.01, "1¢"), (0.1, "10¢"), (1.0, "$1")):
        x = X(c)
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{T+ph}" stroke="var(--grid)" stroke-width="1"/>'
                   f'<text x="{x:.1f}" y="{T+ph+18}" text-anchor="middle" font-size="12" fill="var(--ink-2)">{lab}</text>')
    out.append(f'<text x="{L+pw/2:.0f}" y="{H-6}" text-anchor="middle" font-size="12" fill="var(--ink-3)">mean cost per case, list price, log scale</text>')
    out.append(f'<text transform="translate(14 {T+ph/2:.0f}) rotate(-90)" text-anchor="middle" font-size="12" fill="var(--ink-3)">hidden-test pass rate</text>')
    placed = []
    for c in sorted(cfgs, key=lambda c: by[c]["cost"] / by[c]["n"]):
        a = by[c]
        cost, pr = a["cost"] / a["n"], a["p"] / a["n"]
        x, y = X(cost), Y(pr)
        dy = -12
        for (px, py, pdy) in placed:
            if abs(px - x) < 72 and abs(py - y) < 6 and pdy == dy:
                dy = 21
        placed.append((x, y, dy))
        col = f"var(--{tier(c)})"
        lab = f"{pr:.0%} pass, {fmt_cost(cost)} per case, {a['n']} case-runs over {len(a['reps'])} replication(s)"
        out.append(f'<g><circle class="hit" cx="{x:.1f}" cy="{y:.1f}" r="14" data-v="{esc(pretty(c))}" data-l="{esc(lab)}"/>'
                   f'<circle class="mark" cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{col}" stroke="var(--surface)" stroke-width="2"/>'
                   f'<text x="{x:.1f}" y="{y+dy:.1f}" text-anchor="middle" font-size="11.5" fill="var(--ink)">{esc(pretty(c))}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


def bar_chart(items, vmax, fmt, label_w=200, log=False, vmin=None):
    """Horizontal bars, <=24px thick, 4px rounded data end, square at the baseline. items: (label, value, tier, tooltip)."""
    bh, gap, L, R, W = 22, 10, label_w, 90, 980
    H = len(items) * (bh + gap) + 8
    pw = W - L - R
    if log:
        lo, hi = math.log10(vmin), math.log10(vmax)

        def wfor(v):
            return 0 if v <= 0 else max(2, (math.log10(v) - lo) / (hi - lo) * pw)
    else:
        def wfor(v):
            return 0 if v <= 0 else v / vmax * pw
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="bar chart">']
    for i, (lab, v, t, tipt) in enumerate(items):
        y = 4 + i * (bh + gap)
        w = wfor(v)
        col = f"var(--{t})"
        out.append(f'<text x="{L-10}" y="{y+bh*0.72:.1f}" text-anchor="end" font-size="12.5" fill="var(--ink)">{esc(lab)}</text>')
        out.append(f'<rect class="hit" x="{L}" y="{y-gap/2}" width="{pw+R}" height="{bh+gap}" data-v="{esc(fmt(v))}" data-l="{esc(tipt)}"/>')
        if w > 4:
            out.append(f'<path class="mark" d="M{L},{y} h{w-4:.1f} a4,4 0 0 1 4,4 v{bh-8} a4,4 0 0 1 -4,4 h-{w-4:.1f} z" fill="{col}"/>')
        else:
            out.append(f'<rect class="mark" x="{L}" y="{y}" width="3" height="{bh}" fill="{col}"/>')
        out.append(f'<text x="{L+w+8:.1f}" y="{y+bh*0.72:.1f}" font-size="12" fill="var(--ink-2)">{esc(fmt(v))}</text>')
    out.append("</svg>")
    return "\n".join(out)


def heatmap(spec, cfgs, tiers):
    """Pass rate per configuration and tier. One sequential hue; the value is printed in every cell."""
    cw, ch, L, T = 118, 30, 200, 34
    W = L + cw * len(tiers) + 10
    H = T + ch * len(cfgs) + 6
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Pass rate per tier and configuration">']
    for j, t in enumerate(tiers):
        out.append(f'<text x="{L+j*cw+cw/2:.0f}" y="22" text-anchor="middle" font-size="12" fill="var(--ink-2)">T{t} {esc(TIER_NAMES[t])}</text>')
    for i, c in enumerate(cfgs):
        y = T + i * ch
        out.append(f'<text x="{L-10}" y="{y+ch*0.68:.1f}" text-anchor="end" font-size="12.5" fill="var(--ink)">{esc(pretty(c))}</text>')
        for j, t in enumerate(tiers):
            rs = [r for r in spec if r["config"] == c and r["tier"] == t]
            x = L + j * cw
            if not rs:
                out.append(f'<rect x="{x+1}" y="{y+1}" width="{cw-2}" height="{ch-2}" fill="var(--surface-2)"/>')
                continue
            pr = sum(r["passed"] for r in rs) / len(rs)
            step = "--seq-4" if pr >= 0.999 else "--seq-3" if pr >= 0.9 else "--seq-2" if pr >= 0.8 else "--seq-1"
            ink = "var(--surface)" if pr >= 0.9 else "var(--ink)"
            fails = sorted({r["task"] for r in rs if not r["passed"]})
            tipt = f"{pretty(c)}, tier {t} {TIER_NAMES[t]}: {sum(r['passed'] for r in rs)} of {len(rs)} case-runs passed" + (f". Missed: {', '.join(fails)}" if fails else "")
            out.append(f'<rect class="mark" x="{x+1}" y="{y+1}" width="{cw-2}" height="{ch-2}" fill="var({step})" data-v="{pr:.0%}" data-l="{esc(tipt)}"/>'
                       f'<text x="{x+cw/2:.0f}" y="{y+ch*0.68:.1f}" text-anchor="middle" font-size="12" fill="{ink}" pointer-events="none">{pr:.0%}</text>')
    out.append("</svg>")
    return "\n".join(out)


def table(header, rows, numeric=()):
    th = "".join(f'<th class="{"num" if i in numeric else ""}">{esc(h)}</th>' for i, h in enumerate(header))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i in numeric else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>"


def swatch(cfg):
    return f'<span class="swatch" style="background:var(--{tier(cfg)})"></span>{esc(pretty(cfg))}'


def legend():
    return '<div class="legend">' + "".join(f'<span style="--c:var(--{k})">{esc(v)}</span>' for k, v in TIER_LABEL.items()) + "</div>"


def run_status(name, n_cases, expected):
    if name.startswith("smoke"):
        return "pilot"
    if expected and n_cases < expected:
        return "partial"
    return "complete"


# ----------------------------------------------------------------------------- page
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    args = ap.parse_args()
    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    (out / "runs").mkdir(parents=True)
    S, runs, spec, tickets, by = load()
    full = [c for c in by if len(by[c]["tasks"]) >= 21]
    for c in by:
        if len(by[c]["tasks"]) < 21:
            SUFFIX[c] = " (hard subset)" if by[c]["tasks"] == HARD else " (partial)"
    order = sorted(full, key=lambda c: by[c]["cost"] / by[c]["n"])
    all_order = sorted(by, key=lambda c: by[c]["cost"] / by[c]["n"])
    tiers = sorted({r["tier"] for r in spec})
    paid = [c for c in order if by[c]["cost"] > 0]

    # run reports (everything that has one), compare reports
    run_rows = []
    for d in sorted(RUNS.iterdir()):
        if not (d / "report.html").exists():
            continue
        R = json.loads((d / "run_result.json").read_text())
        shutil.copy(d / "report.html", out / "runs" / f"{d.name}.html")
        n = R.get("num_cases") or len(R.get("per_case", {}))
        cost = R.get("cost_usd")
        expected = 24 if "hard" not in d.name else 11
        st = run_status(d.name, n, expected)
        pill = "" if st == "complete" else f'<span class="pill">{st}</span>'
        run_rows.append([f'<a href="runs/{esc(d.name)}.html">{esc(d.name)}</a>{pill}', esc(R.get("model")), esc((R.get("eval_params") or {}).get("effort", "")),
                         esc(R.get("agent")), str(n), "" if cost is None else fmt_cost(cost)])
    compares = []
    for cfg_dir in sorted(ANOVA.glob("*/compare")):
        name = cfg_dir.parent.name
        shutil.copytree(cfg_dir, out / "compare" / name)
        aj = cfg_dir.parent / "model-routing-eval" / "anova.json"
        compares.append((name, json.loads(aj.read_text()) if aj.exists() else None))

    # ---- hero tiles
    cheapest, priciest = paid[0], paid[-1]
    ratio = (by[priciest]["cost"] / by[priciest]["n"]) / (by[cheapest]["cost"] / by[cheapest]["n"])
    tiles = [(str(S["n_runs"]), "recorded case-runs"), (str(S["n_tasks"]), "tasks in six tiers"), (str(len(by)), "model and effort configurations"),
             (f"{by[cheapest]['p']/by[cheapest]['n']:.0%}", f"pass rate of the cheapest paid config, {pretty(cheapest)}"),
             (f"{ratio:.0f}x", f"cost gap, {pretty(priciest)} vs {pretty(cheapest)}, same tasks")]
    tiles_html = '<div class="tiles">' + "".join(f'<div class="tile"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div></div>' for v, l in tiles) + "</div>"

    fig1 = f'<figure><figcaption>Pass rate vs cost per case</figcaption><div class="sub">Spec tasks with hidden tests, configurations that ran the full set. Hover a dot for replications.</div>{dot_chart(by, order)}{legend()}</figure>'
    items = [(pretty(c), by[c]["cost"] / by[c]["n"], tier(c), f"{by[c]['n']} case-runs, {by[c]['p']/by[c]['n']:.0%} pass, {by[c]['wall']/by[c]['n']:.0f} s mean wall time") for c in all_order]
    fig2 = f'<figure><figcaption>Mean cost per case</figcaption><div class="sub">List prices, October 2026. Log scale. GLM via EnMaaS is free.</div>{bar_chart(items, 2.0, fmt_cost, log=True, vmin=0.002)}{legend()}</figure>'
    fig3 = f'<figure><figcaption>Pass rate by tier</figcaption><div class="sub">Hidden-test pass rate per configuration and task tier. Hover a cell for the missed tasks.</div>{heatmap(spec, all_order, tiers)}</figure>'
    fig4 = ""
    if tickets:
        tq = defaultdict(list)
        for r in tickets:
            tq[r["config"]].append(r)
        titems = []
        for c in sorted(tq, key=lambda c: sum(r["quality"] for r in tq[c]) / len(tq[c]), reverse=True):
            rs = tq[c]
            m = sum(r["quality"] for r in rs) / len(rs)
            per = defaultdict(list)
            for r in rs:
                per[r["task"]].append(r["quality"])
            detail = ", ".join(f"{t.replace('_fromager_', ' ').replace('_ticket', '')} {sum(v)/len(v):.1f}" for t, v in sorted(per.items()))
            titems.append((pretty(c), m, tier(c), f"{len(rs)} judged runs, {fmt_cost(sum(r['cost'] for r in rs)/len(rs))} per case. {detail}"))
        fig4 = f'<figure><figcaption>Ticket-only tasks: judge score against the merged PR</figcaption><div class="sub">Three real fromager issues given as plain issue text. Claude Opus 5.5 scores the diff against the merged PR, 1 to 5. Hover for per-task scores.</div>{bar_chart(titems, 5.0, lambda v: f"{v:.2f}")}{legend()}</figure>'
    witems = [(pretty(c), by[c]["wall"] / by[c]["n"], tier(c), "mean wall time per case, hidden tests excluded") for c in sorted(all_order, key=lambda c: by[c]["wall"] / by[c]["n"])]
    fig5 = f'<figure><figcaption>Mean wall time per case</figcaption><div class="sub">Seconds from prompt to agent exit.</div>{bar_chart(witems, max(v for _, v, _, _ in witems), lambda v: f"{v:.0f} s")}{legend()}</figure>'

    rows = []
    for c in all_order:
        a = by[c]
        rows.append([swatch(c), f"{a['n']} ({len(a['reps'])})", f"{a['p']/a['n']:.0%}", fmt_cost(a["cost"] / a["n"]), f"{a['wall']/a['n']:.0f} s", str(len(a["tasks"]))])
    t_headline = table(["configuration", "case-runs (reps)", "pass", "cost / case", "wall", "tasks"], rows, numeric=(1, 2, 3, 4, 5))
    pairs = [("gpt-6-luna@low", "gpt-6-luna@xhigh"), ("gpt-6.1-sol@low", "gpt-6.1-sol@xhigh"), ("haiku-5-5@low", "haiku-5-5@medium"), ("sonnet-5-5@low", "sonnet-5-5@medium")]
    erows = []
    for lo, hi in pairs:
        if lo in by and hi in by:
            a, b = by[lo], by[hi]
            erows.append([esc(pretty(lo).rsplit(" ", 1)[0]), f"{lo.split('@')[1]} ({len(a['reps'])}) vs {hi.split('@')[1]} ({len(b['reps'])})",
                          f"{a['p']/a['n']:.0%} vs {b['p']/b['n']:.0%}", f"{fmt_cost(a['cost']/a['n'])} vs {fmt_cost(b['cost']/b['n'])}", f"{a['wall']/a['n']:.0f} s vs {b['wall']/b['n']:.0f} s"])
    t_effort = table(["model", "effort (reps)", "pass rate", "cost / case", "wall"], erows) if erows else ""
    anova_html = ""
    for name, A in compares:
        if not A:
            continue
        pv, sig = A["anova"]["p_values"], A["anova"]["significant"]
        crow = []
        for c in sorted(A["condition_summaries"], key=lambda c: c.get("cost") or 0):
            lv = c["levels"]
            cfg = f"{lv['model'].replace('claude-', '')}@{lv['effort']}"
            crow.append([swatch(cfg), f"{c['mean']:.1%}", f"{c['std']:.2f}", str(c["n"]), fmt_cost(c.get("cost", 0))])
        verdict = "; ".join(f"{k}: p = {v:.2f} ({'significant' if sig.get(k) else 'not significant'})" for k, v in pv.items())
        pareto = ", ".join(pretty(f"{p['levels']['model'].replace('claude-', '')}@{p['levels']['effort']}") for p in A["pareto_frontier"])
        anova_html += (f"<h3>{esc(name)}: mixed-effects ANOVA over pass per case-run</h3>" + table(["condition", "pass mean", "std", "case-runs", "cost / run"], crow, numeric=(1, 2, 3, 4))
                       + f"<p><b>Verdict:</b> {esc(verdict)}. Holm-corrected. <b>Pareto frontier:</b> {esc(pareto)}. "
                       f'<a href="compare/{esc(name)}/index.html">Open the eval-compare report</a>.</p>')
    reps = defaultdict(dict)
    for r in spec:
        reps[(r["config"], r["task"])][r["rep"]] = r["passed"]
    flips = sorted((c, t) for (c, t), v in reps.items() if len(v) >= 2 and len(set(v.values())) > 1)
    t_noise = table(["configuration", "task", "replications"], [[swatch(c), esc(t), "pass / fail"] for c, t in flips]) if flips else "<p>No disagreements between replications.</p>"
    md_block = "<pre style='white-space:pre-wrap;font-size:.8rem;color:var(--ink-2)'>" + esc((RESULTS / "report" / "summary.md").read_text()) + "</pre>"

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>model-routing-eval results</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>
<h1>Which model, at which effort, for which task</h1><div class="rule"></div>
<p class="lede">The same coding tasks, run headlessly through real coding agents on every model tier we have. Hidden tests decide pass or fail;
for real-repository tasks Claude Opus 5.5 also scores the diff against the merged PR. Built with
<a href="https://github.com/opendatahub-io/agent-eval-harness">agent-eval-harness</a>; source, tasks and raw records at
<a href="https://github.com/andre-motta/model-routing-eval">github.com/andre-motta/model-routing-eval</a>.</p>
{tiles_html}
<p class="note">Costs are list prices, October 2026, from token usage. Claude Code reports its own cost; Codex runs are priced from the repository rate
table; GLM 5.3 via the EnMaaS gateway is free. Configurations are model@effort. Colour follows the price tier.</p>

<h2>Results</h2>
{fig1}
{fig2}
{fig3}
{fig4}
{fig5}

<h2>Tables</h2>
<h3>All configurations</h3>{t_headline}
<h3>Effort, same model</h3>{t_effort}
{anova_html}
<h3>Replications that disagreed</h3>{t_noise}
<details><summary>Analyzer summary (per tier and config, cheapest passing config per task)</summary>{md_block}</details>

<h2>Per-run reports</h2>
<p class="note">Every run, including pilots and runs cut short. Each report has the run configuration, token and cache metrics, per-case scores with judge rationales, and the agent transcripts.</p>
{table(["run", "model", "effort", "agent", "cases", "cost"], run_rows, numeric=(4, 5))}
<p class="note">Built by <code>harness/build_site.py</code>. Hover or focus any mark for details; every value is also in the tables.</p>
<script>{JS}</script></body></html>"""
    (out / "index.html").write_text(page)
    (out / ".nojekyll").write_text("")
    print(f"site: {out} ({len(run_rows)} run reports, {len(compares)} compare reports)")


if __name__ == "__main__":
    main()
