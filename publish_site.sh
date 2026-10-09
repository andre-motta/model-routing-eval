#!/usr/bin/env bash
# Rebuild the results site and publish it to the gh-pages branch (GitHub Pages).
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python harness/build_site.py --out site
W=$PWD/.work/gh-pages
/bin/rm -rf "$W"; git worktree prune
git worktree add -q --detach "$W"
( cd "$W" && git checkout -q --orphan gh-pages && git rm -rfq . && cp -r ../../site/. . && git add -A \
  && git commit -q -m "Results site $(date +%Y-%m-%d)" && git push -q -f origin gh-pages )
git worktree remove --force "$W"
echo "published: https://alustos.us/model-routing-eval/"
