#!/usr/bin/env bash
# One-shot setup: venv, this package, agent-eval-harness at a pinned commit with local patches applied.
#   ./setup.sh            # uses .deps/agent-eval-harness
#   HARNESS_DIR=~/git/opendatahub-io/agent-eval-harness ./setup.sh   # use an existing clone (patches not applied)
set -euo pipefail
cd "$(dirname "$0")"
HARNESS_REPO=${HARNESS_REPO:-https://github.com/opendatahub-io/agent-eval-harness.git}
HARNESS_COMMIT=${HARNESS_COMMIT:-bf531fc042d1c0391da241cd55ee4281621b891c}
HARNESS_DIR=${HARNESS_DIR:-}

[ -d .venv ] || uv venv -q .venv
if [ -z "$HARNESS_DIR" ]; then
  HARNESS_DIR=.deps/agent-eval-harness
  if [ ! -d "$HARNESS_DIR/.git" ]; then
    mkdir -p .deps && git clone -q "$HARNESS_REPO" "$HARNESS_DIR"
  fi
  git -C "$HARNESS_DIR" fetch -q origin && git -C "$HARNESS_DIR" checkout -q "$HARNESS_COMMIT"
  # Local patches: each one is skipped when upstream already contains it (git apply --check fails cleanly).
  for p in patches/*.patch; do
    [ -e "$p" ] || continue
    if git -C "$HARNESS_DIR" apply --check "$PWD/$p" 2>/dev/null; then
      git -C "$HARNESS_DIR" apply "$PWD/$p" && echo "applied $p"
    else
      echo "skipped $p (already applied upstream or does not apply at $HARNESS_COMMIT)"
    fi
  done
fi
VIRTUAL_ENV=.venv uv pip install -q -e . -e "$HARNESS_DIR[mlflow,anova]" litellm
.venv/bin/python harness/export_cases.py
echo "ready: .venv, harness at $HARNESS_DIR ($(git -C "$HARNESS_DIR" rev-parse --short HEAD)), run ./run_eval.sh <model> <effort>"
