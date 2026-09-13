#!/usr/bin/env bash
# Fail when a plugin's files changed on this branch but its own version did not move.
#
# `claude plugin update` only refreshes what a client has cached when a plugin's version
# changes — a content-only edit with no version bump ships silently stale until someone
# remembers to bump it by hand in a follow-up commit. That is not hypothetical: 920be91 in
# this repo's own history exists solely because 1f4dfda's fix did not take until a second
# commit bumped memory-sync's version.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BASE="${1:?usage: check-plugin-version-bump.sh <base-ref>, e.g. origin/main}"

if ! git rev-parse --verify --quiet "$BASE" >/dev/null; then
  echo "base ref '$BASE' not found -- fetch it first (git fetch origin main)" >&2
  exit 1
fi

MERGE_BASE="$(git merge-base "$BASE" HEAD)"

status=0
for plugin_json in plugins/*/.claude-plugin/plugin.json; do
  plugin_dir="$(dirname "$(dirname "$plugin_json")")"
  name="$(basename "$plugin_dir")"

  changed="$(git diff --name-only "$MERGE_BASE" HEAD -- "$plugin_dir")"
  if [ -z "$changed" ]; then
    continue
  fi

  old_version="$(git show "$MERGE_BASE:$plugin_json" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version",""))' 2>/dev/null || true)"
  new_version="$(python3 -c 'import json; print(json.load(open("'"$plugin_json"'")).get("version",""))')"

  if [ "$old_version" = "$new_version" ]; then
    echo "FAIL: $name changed but plugin.json version is still $new_version" >&2
    echo "$changed" | sed 's/^/    /' >&2
    status=1
  else
    echo "ok: $name ${old_version:-<new plugin>} -> $new_version"
  fi
done

exit "$status"
