#!/usr/bin/env python3
"""Tables and charts from results/. Usage: python harness/analyze.py results/ --out results/report"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

TIER_NAMES = {1: "Mechanical", 2: "Bounded impl", 3: "Debugging", 4: "Architecture", 5: "Long context"}


def load(root: Path) -> pd.DataFrame:
    rows = []
    for f in root.rglob("*.json"):
        if "/work/" in str(f):
            continue
        d = json.loads(f.read_text())
        tk = d.get("tokens") or {}
        rows.append(dict(task=d["task"], tier=d["tier"], backend=d["backend"], model=d["model"], effort=d["effort"],
                         rep=d["rep"], passed=bool(d["passed"]), cost=d.get("cost_usd") or 0.0, wall=d.get("wall_s", 0),
                         turns=d.get("turns", 0), tok_in=tk.get("input", 0), tok_cached=tk.get("cached", 0),
                         tok_out=tk.get("output", 0), tok_reason=tk.get("reasoning", 0), error=d.get("error")))
    if not rows:
        raise SystemExit(f"no records under {root}")
    df = pd.DataFrame(rows)
    df["config"] = df["model"].str.replace("claude-", "").str.replace("-20251001", "") + "@" + df["effort"]
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = Path(args.root)
    out = Path(args.out or root / "report")
    out.mkdir(parents=True, exist_ok=True)
    df = load(root)
    df.to_csv(out / "runs.csv", index=False)

    md = ["# Results\n", f"{len(df)} runs, {df.task.nunique()} tasks, {df.config.nunique()} configs\n"]

    # 1. pass rate and mean cost per config per tier
    g = df.groupby(["tier", "config"]).agg(pass_rate=("passed", "mean"), mean_cost=("cost", "mean"),
                                           mean_wall=("wall", "mean"), n=("passed", "size")).reset_index()
    md.append("## Pass rate and mean cost per config, by tier\n")
    for tier, sub in g.groupby("tier"):
        md.append(f"### Tier {tier}: {TIER_NAMES.get(tier, '')}\n")
        md.append("| config | pass rate | mean cost | mean wall s | n |\n|---|---|---|---|---|")
        for _, r in sub.sort_values("mean_cost").iterrows():
            md.append(f"| {r.config} | {r.pass_rate:.0%} | ${r.mean_cost:.3f} | {r.mean_wall:.0f} | {r.n} |")
        md.append("")

    # 2. cheapest config that passes every rep of a task
    md.append("## Cheapest config that passed every repetition, per task\n")
    md.append("| task | tier | cheapest passing config | cost | most expensive passing | cost | saving |\n|---|---|---|---|---|---|---|")
    per = df.groupby(["task", "tier", "config"]).agg(all_pass=("passed", "all"), cost=("cost", "mean")).reset_index()
    for (task, tier), sub in per.groupby(["task", "tier"]):
        ok = sub[sub.all_pass].sort_values("cost")
        if ok.empty:
            md.append(f"| {task} | {tier} | none passed | | | | |")
            continue
        lo, hi = ok.iloc[0], ok.iloc[-1]
        saving = 1 - lo.cost / hi.cost if hi.cost else 0
        md.append(f"| {task} | {tier} | {lo.config} | ${lo.cost:.3f} | {hi.config} | ${hi.cost:.3f} | {saving:.0%} |")
    md.append("")

    # 3. routing scenario: route each tier to its cheapest fully-passing config vs. everything on the priciest config
    md.append("## Routing scenario\n")
    cfg_cost = df.groupby("config").cost.sum().sort_values()
    priciest = df.groupby("config").cost.mean().idxmax()
    base = df[df.config == priciest]
    routed_cost, routed_pass = 0.0, 0
    for tier, sub in per.groupby("tier"):
        ok = sub[sub.all_pass]
        if ok.empty:
            continue
        best = ok.groupby("config").cost.mean().idxmin()
        routed_cost += ok[ok.config == best].cost.sum()
        routed_pass += len(ok[ok.config == best])
    md.append(f"Everything on `{priciest}`: ${base.cost.sum():.2f} for {base.passed.mean():.0%} pass rate "
              f"({len(base)} runs).")
    md.append(f"Routed per tier to the cheapest fully-passing config: ${routed_cost:.2f} for {routed_pass} passing tasks.\n")

    (out / "summary.md").write_text("\n".join(md))

    # charts
    fig, ax = plt.subplots(figsize=(9, 5))
    for cfg, sub in g.groupby("config"):
        ax.scatter(sub.mean_cost, sub.pass_rate, label=cfg, s=60)
        for _, r in sub.iterrows():
            ax.annotate(f"T{r.tier}", (r.mean_cost, r.pass_rate), fontsize=7, xytext=(3, 3), textcoords="offset points")
    ax.set_xscale("log"); ax.set_xlabel("mean cost per run, USD (log)"); ax.set_ylabel("pass rate")
    ax.set_title("Quality vs cost, one point per config and tier"); ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(out / "quality_vs_cost.png", dpi=160)

    fig, ax = plt.subplots(figsize=(10, 5))
    piv = df.pivot_table(index="task", columns="config", values="cost", aggfunc="mean")
    piv.plot.bar(ax=ax, logy=True); ax.set_ylabel("mean cost per run, USD (log)"); ax.set_title("Cost per task per config")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(out / "cost_per_task.png", dpi=160)

    fig, ax = plt.subplots(figsize=(10, 5))
    piv = df.pivot_table(index="task", columns="config", values="passed", aggfunc="mean")
    piv.plot.bar(ax=ax); ax.set_ylabel("pass rate"); ax.set_title("Pass rate per task per config")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(out / "pass_per_task.png", dpi=160)
    print(f"wrote {out}/summary.md, runs.csv and 3 charts")


if __name__ == "__main__":
    main()
