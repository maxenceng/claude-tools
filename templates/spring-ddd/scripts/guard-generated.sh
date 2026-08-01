#!/usr/bin/env bash
# PreToolUse guard. Blocks edits to generated or build output, which are overwritten
# on the next build — editing them wastes a turn and hides the real change.
# Exit 2 tells Claude Code to block the call and show stderr to the model.
set -uo pipefail

payload="$(cat)"

file_path="$(printf '%s' "${payload}" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null)"

[[ -z "${file_path}" ]] && exit 0

case "${file_path}" in
	*/target/*)
		echo "Refusing to edit build output (${file_path}). Change the source instead." >&2
		exit 2
		;;
	*/src/api/generated/*)
		echo "Refusing to edit the generated API client (${file_path}). It is rebuilt from the OpenAPI schema — change the backend annotation and run 'make openapi-client'." >&2
		exit 2
		;;
	*/node_modules/*)
		echo "Refusing to edit a dependency (${file_path})." >&2
		exit 2
		;;
esac

exit 0
