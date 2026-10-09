#!/usr/bin/env python3
"""Build a static site for GitHub Pages from the results: index with the summary tables and charts,
the eval-anova compare report(s), and every per-run harness report.

  python harness/build_site.py --out site
"""
import argparse
import html
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from harness.run import ROOT  # noqa: E402

RUNS = ROOT / "eval" / "runs" / "model-routing-eval"
ANOVA = ROOT / "eval" / "anova"
RESULTS = ROOT / "results" / "harness"

CSS = """
body{font-family:'Red Hat Text',system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#151515;line-height:1.45}
h1,h2,h3{font-family:'Red Hat Display',system-ui,sans-serif} h1{border-bottom:3px solid #e00;padding-bottom:.3rem}
table{border-collapse:collapse;margin:1rem 0;font-size:.92rem} th,td{border-bottom:1px solid #d2d2d2;padding:.35rem .6rem;text-align:left}
th{color:#6a6e73;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em} tr:nth-child(even) td{background:#f5f5f5}
a{color:#06c} .note{color:#6a6e73;font-size:.9rem} img{max-width:100%;border:1px solid #d2d2d2;margin:.5rem 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:.6rem} .card{border:1px solid #d2d2d2;border-top:4px solid #e00;padding:.7rem}
code{background:#f5f5f5;padding:.1rem .3rem}
"""


def md_table_to_html(md_lines):
    rows = [ln.strip().strip("|").split("|") for ln in md_lines if ln.startswith("|")]
    rows = [[c.strip() for c in r] for r in rows if not set("".join(r)) <= set("-| ")]
    if not rows:
        return ""
    out = ["<table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in rows[0]) + "</tr>"]
    for r in rows[1:]:
        out.append("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>")
    return "\n".join(out) + "</table>"


def summary_html():
    md = (RESULTS / "report" / "summary.md").read_text().splitlines()
    parts, buf, heading = [], [], None
    def flush():
        if heading:
            parts.append(f"<h3>{html.escape(heading)}</h3>")
        parts.append(md_table_to_html(buf))
    for ln in md + ["## end"]:
        if ln.startswith("## ") or ln.startswith("### "):
            if buf or heading:
                flush()
            buf, heading = [], ln.lstrip("# ").strip()
            if ln.startswith("## "):
                parts.append(f"<h2>{html.escape(heading)}</h2>"); heading = None
        elif ln.startswith("|"):
            buf.append(ln)
        elif ln.strip() and not ln.startswith("#") and heading is None and not buf:
            parts.append(f"<p class='note'>{html.escape(ln)}</p>")
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "site"))
    args = ap.parse_args()
    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    (out / "runs").mkdir(parents=True)
    (out / "charts").mkdir()
    for png in (RESULTS / "report").glob("*.png"):
        shutil.copy(png, out / "charts" / png.name)
    runs = []
    for d in sorted(RUNS.iterdir()):
        if d.name.startswith("smoke") or not (d / "report.html").exists():
            continue
        R = json.loads((d / "run_result.json").read_text())
        shutil.copy(d / "report.html", out / "runs" / f"{d.name}.html")
        runs.append((d.name, R.get("model"), (R.get("eval_params") or {}).get("effort", ""), R.get("agent"),
                     R.get("num_cases") or len(R.get("per_case", {})), R.get("cost_usd")))
    compares = []
    for cfg_dir in sorted(ANOVA.glob("*/compare")):
        name = cfg_dir.parent.name
        shutil.copytree(cfg_dir, out / "compare" / name)
        compares.append(name)
    S = json.loads((RESULTS / "report" / "summary.json").read_text())
    run_rows = "".join(f"<tr><td><a href='runs/{html.escape(n)}.html'>{html.escape(n)}</a></td><td>{html.escape(str(m))}</td><td>{html.escape(str(e))}</td>"
                       f"<td>{html.escape(str(a))}</td><td>{c}</td><td>{'' if cost is None else f'${cost:.2f}'}</td></tr>" for n, m, e, a, c, cost in runs)
    cmp_cards = "".join(f"<div class='card'><b>eval-anova report</b><br><a href='compare/{html.escape(c)}/index.html'>{html.escape(c)}</a>"
                        f"<p class='note'>Model x effort grid with replications, ANOVA verdict, Pareto frontier.</p></div>" for c in compares)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>model-routing-eval results</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head><body>
<h1>model-routing-eval: results</h1>
<p>Cheapest (model, reasoning effort) that still passes, per coding-task tier. {S['n_runs']} recorded case-runs over {S['n_tasks']} tasks,
{len(S['configs'])} configurations, run through <a href="https://github.com/opendatahub-io/agent-eval-harness">agent-eval-harness</a>.
Source, tasks and raw records: <a href="https://github.com/andre-motta/model-routing-eval">github.com/andre-motta/model-routing-eval</a>.</p>
<p class="note">Costs are list prices (October 2026) computed from token usage. Anthropic runs report their own cost; Codex runs are priced from the
repository's rate table; GLM 5.3 via EnMaaS is free. Hidden tests judge pass or fail; real-repository tasks are also scored 1 to 5 by Claude Opus 5.5
against the merged PR. Configurations are labelled model@effort.</p>
<h2>Comparison reports</h2><div class="grid">{cmp_cards}</div>
<h2>Charts</h2>
<img src="charts/quality_vs_cost.png" alt="quality vs cost"><img src="charts/cost_per_task.png" alt="cost per task"><img src="charts/pass_per_task.png" alt="pass per task">
{summary_html()}
<h2>Per-run reports</h2><p class="note">Each report has the run configuration, token and cache metrics, per-case scores with judge rationales, and the agent transcripts.</p>
<table><tr><th>run</th><th>model</th><th>effort</th><th>agent</th><th>cases</th><th>cost</th></tr>{run_rows}</table>
<p class="note">Built by <code>harness/build_site.py</code>.</p></body></html>"""
    (out / "index.html").write_text(page)
    (out / ".nojekyll").write_text("")
    print(f"site: {out} ({len(runs)} run reports, {len(compares)} compare reports)")


if __name__ == "__main__":
    main()
