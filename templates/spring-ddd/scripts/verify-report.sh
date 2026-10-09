#!/usr/bin/env bash
# Captures make's own exit code: a pipeline reports the last command's status instead, which
# is how a red build gets read as green.
set -uo pipefail

LOG="${VERIFY_LOG:-target/verify.log}"
mkdir -p "$(dirname "$LOG")"

make verify > "$LOG" 2>&1
status=$?

echo "exit     $status"
# Matched by shape, not by a list of names: a hardcoded list silently omits a step added to
# `verify` later, and reports five of six as though that were the whole pipeline.
grep -E '^make [a-z][a-z-]*$' "$LOG" | sed 's/^make /step     /'
grep -E '^\[INFO\] Tests run: .*Skipped: [0-9]+$' "$LOG" | tail -1 | sed 's/^\[INFO\] /tests    /'

if [ "$status" -ne 0 ]; then
    echo
    echo "first failures:"
    grep -nE '<<< (FAILURE|ERROR)|BUILD FAILURE|^\[ERROR\] .*\.java' "$LOG" | head -5
fi

echo
echo "log      $LOG"
exit "$status"
