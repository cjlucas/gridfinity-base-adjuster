#!/bin/bash
# Shared logic behind both Finder Quick Actions. Called as:
#   run-quickaction.sh <python-module> <output-suffix> <file>...
# e.g. run-quickaction.sh gfbadjust _21mm /path/to/Bin.stl
#
# Lives in the repo (not embedded in the .workflow's plist) so it's a
# normal, diffable, testable shell script -- the .workflow's own "Run
# Shell Script" action is just a one-line call into this file.

set -u

MODULE="$1"
SUFFIX="$2"
shift 2

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$HOME/Library/Logs/GridfinityAdjuster"
mkdir -p "$LOG_DIR"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

successes=()
failures=()
skipped=()

for input in "$@"; do
  base="$(basename "$input")"

  if [ -d "$input" ]; then
    skipped+=("$base (folder)")
    continue
  fi
  case "$base" in
    *.[Ss][Tt][Ll]) ;;
    *) skipped+=("$base (not an STL)"); continue ;;
  esac

  dir="$(dirname "$input")"
  stem="${base%.*}"
  output="$dir/${stem}${SUFFIX}.stl"
  log_file="$LOG_DIR/${MODULE}-${TIMESTAMP}-${stem}.log"

  if ( cd "$REPO_DIR" && /usr/bin/python3 -m "$MODULE" "$input" -o "$output" -v ) >"$log_file" 2>&1; then
    successes+=("$base -> $(basename "$output")")
  else
    reason="$(grep -v '^[[:space:]]*$' "$log_file" | tail -1)"
    failures+=("$base: ${reason:-see log} ($log_file)")
  fi
done

title="Gridfinity Base Adjuster"
if [ "$MODULE" = "gfladjust" ]; then
  title="Gridfinity Lip Remover"
fi

total=$(( ${#successes[@]} + ${#failures[@]} + ${#skipped[@]} ))

if [ "$total" -eq 1 ] && [ "${#successes[@]}" -eq 1 ]; then
  message="${successes[0]}"
elif [ "$total" -eq 1 ] && [ "${#failures[@]}" -eq 1 ]; then
  message="Failed: ${failures[0]}"
elif [ "$total" -eq 1 ] && [ "${#skipped[@]}" -eq 1 ]; then
  message="Skipped: ${skipped[0]}"
else
  parts=()
  [ "${#successes[@]}" -gt 0 ] && parts+=("${#successes[@]} succeeded")
  [ "${#failures[@]}" -gt 0 ] && parts+=("${#failures[@]} failed")
  [ "${#skipped[@]}" -gt 0 ] && parts+=("${#skipped[@]} skipped")
  message="$(IFS=', '; echo "${parts[*]}")"
  if [ "${#failures[@]}" -gt 0 ]; then
    message="$message -- see $LOG_DIR"
  fi
fi

# osascript with -e args (not a single interpolated string) avoids
# breaking on quotes/special characters in filenames.
osascript -e 'on run {theTitle, theMessage}' \
          -e 'display notification theMessage with title theTitle' \
          -e 'end run' \
          -- "$title" "$message" >/dev/null 2>&1

[ "${#failures[@]}" -eq 0 ]
