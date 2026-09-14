#!/bin/bash
# Installs the Gridfinity Finder Quick Actions into ~/Library/Services.
# Safe to re-run any time (e.g. after moving the repo, or to pick up
# changes to the .workflow templates) -- it always reinstalls fresh.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICES_DIR="$HOME/Library/Services"
mkdir -p "$SERVICES_DIR"

WORKFLOWS=(
  "Gridfinity Base Adjuster (21mm).workflow"
  "Gridfinity Remove Stacking Lip.workflow"
)

for wf in "${WORKFLOWS[@]}"; do
  src="$REPO_DIR/macos/$wf"
  dest="$SERVICES_DIR/$wf"
  tmp="$(mktemp -d)"
  cp -R "$src" "$tmp/$wf"
  sed -i '' "s|__REPO_DIR__|$REPO_DIR|g" "$tmp/$wf/Contents/document.wflow"
  rm -rf "$dest"
  cp -R "$tmp/$wf" "$dest"
  rm -rf "$tmp"
  echo "Installed: $dest"
done

echo
echo "Done. The Quick Actions should now appear under Finder's right-click"
echo "-> Quick Actions submenu for any selected file(s). If they don't show"
echo "up immediately, try selecting a file in Finder again or log out/in."
