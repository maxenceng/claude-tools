#!/usr/bin/env bash
# Waits for CI on the current branch's PR and exits on its verdict, so a red pipeline cannot be
# read as "still running". `gh pr checks --watch` exits 8 on failure and 0 when there is no PR.
set -uo pipefail

branch=$(git rev-parse --abbrev-ref HEAD)

number=$(gh pr list --head "$branch" --state open --json number --jq '.[0].number // empty' 2>/dev/null)
if [ -z "$number" ]; then
    echo "no open PR for $branch"
    exit 2
fi

head=$(gh pr view "$number" --json headRefOid --jq '.headRefOid')
local_head=$(git rev-parse HEAD)
if [ "$head" != "$local_head" ]; then
    echo "PR #$number is at ${head:0:7}, you are at ${local_head:0:7} — push before reading CI"
    exit 2
fi

echo "PR #$number  ${head:0:7}  waiting..."
while :; do
    pending=$(gh pr checks "$number" --json bucket --jq '[.[] | select(.bucket == "pending")] | length' 2>/dev/null)
    [ -n "$pending" ] && [ "$pending" = "0" ] && break
    sleep 20
done

gh pr checks "$number" --json name,bucket --jq '.[] | "\(.bucket)\t\(.name)"' | sort

failed=$(gh pr checks "$number" --json bucket --jq '[.[] | select(.bucket != "pass" and .bucket != "skipping")] | length')
if [ "$failed" != "0" ]; then
    echo
    echo "$failed check(s) not green on ${head:0:7}"
    exit 1
fi

echo
echo "all green on ${head:0:7}"
