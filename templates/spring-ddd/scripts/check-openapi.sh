#!/usr/bin/env bash
# Fail if the committed OpenAPI schema no longer matches the running application.
#
# This is the check that catches a whole bug class the compiler cannot. The frontend's
# types come from docs/openapi.json, so if the backend changes and nobody recaptures, the
# frontend still typechecks — against an API that no longer exists. The symptom is a field
# that is `undefined` at runtime while the editor insists it is a string.
#
# Boots the app, captures the schema, and diffs it against the committed one.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

SCHEMA=docs/openapi.json
PORT=8080
LOG="$(mktemp)"
APP_PID=""

cleanup() {
	[[ -n "$APP_PID" ]] && kill "$APP_PID" 2>/dev/null || true
	rm -f "$LOG"
}
trap cleanup EXIT

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

if diff -u "$SCHEMA" "$SCHEMA.actual" > /tmp/openapi.diff 2>&1; then
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
