#!/usr/bin/env bash
# Fail if the committed OpenAPI schema no longer matches the running application.
#
# This is the check that catches a whole bug class the compiler cannot. The frontend's
# types come from docs/openapi.json, so if the backend changes and nobody recaptures, the
# frontend still typechecks — against an API that no longer exists. The symptom is a field
# that is `undefined` at runtime while the editor insists it is a string.
#
# Boots the app, captures the schema, and diffs it against the committed one. Before that
# real diff runs, the same comparison is proven against a deliberately mutated copy of the
# committed schema, so a silently no-op diff cannot let a real mismatch through unnoticed.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

SCHEMA=docs/openapi.json
PORT=8080
LOG="$(mktemp)"
APP_PID=""
MUTATED=""

cleanup() {
	[[ -n "$APP_PID" ]] && kill "$APP_PID" 2>/dev/null || true
	[[ -n "$MUTATED" ]] && rm -f "$MUTATED"
	rm -f "$LOG"
}
trap cleanup EXIT

# The one comparison both the self-test and the real check below run, so proving the
# self-test detects drift proves the real check would too.
schema_matches() {
	diff -u "$1" "$SCHEMA.actual" > /tmp/openapi.diff 2>&1
}

[[ -f "$SCHEMA" ]] || { echo "FAIL: $SCHEMA is not committed. Capture it: make run, make openapi" >&2; exit 1; }

echo "starting the application"
make run >"$LOG" 2>&1 &
APP_PID=$!

for _ in $(seq 1 90); do
	if curl -sf "http://localhost:$PORT/v3/api-docs" -o /dev/null 2>/dev/null; then
		break
	fi
	if ! kill -0 "$APP_PID" 2>/dev/null; then
		echo "FAIL: the application exited before serving the schema" >&2
		tail -30 "$LOG" >&2
		exit 1
	fi
	sleep 2
done

# Normalised the same way `make openapi` writes it, so the diff below is line-by-line
# rather than one enormous line reported as wholly changed.
curl -sf "http://localhost:$PORT/v3/api-docs" \
	| python3 -m json.tool --indent 2 --no-ensure-ascii > "$SCHEMA.actual" \
	|| { echo "FAIL: the application never served /v3/api-docs" >&2; tail -30 "$LOG" >&2; exit 1; }

# Prove the comparison above can detect drift, using the schema this boot already
# captured. The mutation changes a value on an existing line, not an appended one, so a
# comparison weakened to ignore whitespace or drop a field still shows as different.
MUTATED="$(mktemp)"
python3 -c '
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
mutated, count = re.subn(r"(\"title\": \")[^\"]*", r"\1drift-fixture", text, count=1)
if count != 1:
    sys.exit("could not mutate the committed schema: it has no title to change")
open(sys.argv[2], "w", encoding="utf-8").write(mutated)
' "$SCHEMA" "$MUTATED"
if schema_matches "$MUTATED"; then
	echo "FAIL: the drift check did not detect a deliberately mutated schema — the comparison is broken" >&2
	rm -f "$SCHEMA.actual"
	exit 1
fi
echo "ok: the drift check detects a mutated schema"
rm -f "$MUTATED"
MUTATED=""

if schema_matches "$SCHEMA"; then
	rm -f "$SCHEMA.actual" /tmp/openapi.diff
	echo "ok: committed schema matches the running application"
else
	echo "FAIL: $SCHEMA is stale — the running application serves something different." >&2
	echo "Recapture it with: make run, then make openapi, then make openapi-client" >&2
	echo >&2
	head -40 /tmp/openapi.diff >&2
	rm -f "$SCHEMA.actual"
	exit 1
fi
