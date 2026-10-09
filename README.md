# model-routing-eval

Small, reproducible experiment behind the Red Hat AI Enablement session
"Token and Model Cost Optimization". It answers one question per task:

> What is the cheapest (model, reasoning effort) pair that still gets this task right?

Nineteen coding tasks in six difficulty tiers, run headlessly through a real
coding agent (OpenAI Codex CLI or Claude Code), verified by hidden tests,
with tokens, cost and wall time recorded per run.

## Layout

```
tasks/<id>/task.yaml     tier, title, timeout
tasks/<id>/prompt.md     what the agent is told
tasks/<id>/fixture/      the repo the agent works in
tasks/<id>/hidden/       tests copied in AFTER the agent finishes
harness/run.py           run the matrix, one JSON record per run
harness/analyze.py       tables and charts from results/
harness/pricing.py       list prices per 1M tokens
results/                 raw records (committed for the talk)
```

## Tiers

| Tier | Kind | Tasks |
|------|------|-------|
| 1 | Mechanical | rename symbol, ini to toml, add type hints |
| 2 | Bounded implementation | LRU cache, CLI json flag, log parser |
| 3 | Debugging | mutable default, timezone, thread safety, unicode dedupe |
| 4 | Architecture | plugin registry refactor, sync to async migration, backtracking dependency resolver, JSON Patch |
| 5 | Long context | one-cent rounding bug and a quadratic regression, each hidden in a 40-module package |
| 6 | Real repository | three fromager bug fixes (#1146, age filter bypass, #1214), hidden tests are the real PR's tests |

## Run

```bash
uv venv && uv pip install -e .
# dry run: prints the matrix and a cost upper bound, calls nothing
python harness/run.py --backend codex --model gpt-6-luna --effort xhigh --tier 1 2 --dry-run
# real run, 1 repetition
python harness/run.py --backend codex --model gpt-6-luna --effort xhigh --tier 1 2 --reps 1
python harness/run.py --backend claude --model claude-sonnet-5 --effort medium --all --reps 1
# analyze everything under results/
python harness/analyze.py results/ --out results/report
```

Backends:

- `codex`: `codex exec --json` with `-m <model> -c model_reasoning_effort=<effort>`.
  Effort: `none low medium high xhigh max` (model dependent).
- `claude`: `claude -p --output-format json --model <model> --effort <effort>`.
  Effort: `low medium high xhigh max`. Cost comes from Claude Code itself.

Each run gets a fresh copy of the fixture in a temp dir with `git init`, so
the agent cannot see hidden tests or other runs. The diff the agent produced
is saved next to the record.

## Real-repository tasks

Tier 6 tasks have no `fixture/`. `task.yaml` names a `source` repo and commit (the parent
of the real fix), `setup` commands that run before the agent starts (here: create
`.venv` and install the project), `hidden_dest` (where the real PR's test file is
dropped after the agent finishes) and a `verify` command. The repo is cloned once as a
bare mirror under `.cache/repos/` and materialized with `git archive` per run.

Validate any task with:

```bash
python harness/validate_task.py r01_fromager_distinfo --good-commit 3914e3e
```

## Verification

Default: copy `hidden/` into the work dir and run `pytest -q hidden`. A task
can override with `verify.sh` (exit 0 = pass). Hidden tests also assert the
things a lazy solution skips, for example that the old symbol is gone after a
rename, or that a new exporter registers without touching core code.

## Record format

One JSON file per run:

```json
{"task": "t04_lru_cache", "tier": 2, "backend": "codex", "model": "gpt-6-luna",
 "effort": "xhigh", "rep": 0, "passed": true, "wall_s": 41.2, "turns": 7,
 "tokens": {"input": 51230, "cached": 38000, "cache_write": 0, "output": 2210, "reasoning": 1800},
 "cost_usd": 0.0046, "error": null}
```
