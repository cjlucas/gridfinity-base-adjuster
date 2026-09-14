#!/bin/bash
# Removes the Gridfinity Finder Quick Actions from ~/Library/Services.

set -euo pipefail

SERVICES_DIR="$HOME/Library/Services"

WORKFLOWS=(
  "Gridfinity Base Adjuster (21mm).workflow"
  "Gridfinity Remove Stacking Lip.workflow"
)

for wf in "${WORKFLOWS[@]}"; do
  dest="$SERVICES_DIR/$wf"
  if [ -e "$dest" ]; then
    rm -rf "$dest"
    echo "Removed: $dest"
  else
    echo "Not installed: $dest"
  fi
done
