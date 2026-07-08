#!/usr/bin/env bash
# Sync site/ to enaguthi.com (Abhishek21g.github.io gh-pages branch).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${SITE_REPO:-$HOME/Documents/Abhishek21g.github.io}"

if [[ ! -d "$DEST/.git" ]]; then
  echo "error: main site repo not found at $DEST" >&2
  exit 1
fi

cd "$DEST"
git checkout gh-pages
git pull origin gh-pages --no-rebase

mkdir -p vast-docking-workbench/examples
rsync -av --delete "$ROOT/site/" "$DEST/vast-docking-workbench/site/"
cp "$ROOT/examples/haven2-growth-receipt.json" "$DEST/vast-docking-workbench/examples/"
cp "$ROOT/vast-docking-workbench/index.html" "$DEST/vast-docking-workbench/index.html"

git add vast-docking-workbench/
if git diff --cached --quiet; then
  echo "No site changes to publish."
  exit 0
fi

git commit -m "Publish Vast Docking Compatibility Workbench demo"
git pull origin gh-pages --no-rebase
git push origin gh-pages

echo "Published: https://enaguthi.com/vast-docking-workbench/site/"
