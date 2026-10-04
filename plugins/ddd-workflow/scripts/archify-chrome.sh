#!/usr/bin/env bash
# The Chrome archify's browser gate runs in, for /trace-endpoint to hand it as ARCHIFY_CHROME.
#
# archify's `finalize` ends on a real-browser check; with no Chrome it reports "skipped" and exits 2,
# which is not a pass. Playwright's Chromium needs no sudo and stays out of system packages.
#
#   archify-chrome.sh          install (or refresh) Playwright's Chromium, then print its path
#   archify-chrome.sh --path   print the path only; fails when nothing is installed
set -euo pipefail

chrome_path() {
  if [ -n "${ARCHIFY_CHROME:-}" ] && [ -x "$ARCHIFY_CHROME" ]; then
    echo "$ARCHIFY_CHROME"
    return
  fi
  local cache="${PLAYWRIGHT_BROWSERS_PATH:-}"
  if [ -z "$cache" ]; then
    case "$(uname -s)" in
      Darwin) cache="$HOME/Library/Caches/ms-playwright" ;;
      *) cache="$HOME/.cache/ms-playwright" ;;
    esac
  fi
  local found
  found="$(find "$cache" -path '*/chromium-*' -type f \
      \( -name chrome -o -name Chromium -o -name 'Google Chrome for Testing' \) -perm -u+x 2>/dev/null \
    | sort -V | tail -n 1 || true)"
  if [ -z "$found" ]; then
    echo "no Playwright Chromium under $cache -- run $(basename "$0") without arguments first" >&2
    return 1
  fi
  echo "$found"
}

if [ "${1:-}" != "--path" ]; then
  npx --yes playwright install chromium >&2
fi
chrome_path
