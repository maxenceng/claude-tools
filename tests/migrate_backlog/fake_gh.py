#!/usr/bin/env python3
"""A fake `gh` for the backlog-migration tests: a JSON file is the whole of GitHub.

FAKE_GH_STATE names the file. Every call is appended to "calls" before anything else runs, so a
test can assert on what was attempted. "fail_create_at" makes the issue creation with that
1-based ordinal fail the way a dropped connection does, to leave a migration half done.
"""
import json
import os
import re
import sys

STATE = os.environ["FAKE_GH_STATE"]
with open(STATE, encoding="utf-8") as handle:
    state = json.load(handle)
args = sys.argv[1:]
state["calls"].append(args)


def save():
    with open(STATE, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=1)


def fail(message):
    save()
    sys.stderr.write(message + "\n")
    sys.exit(1)


def out(value):
    save()
    sys.stdout.write(value if isinstance(value, str) else json.dumps(value))
    sys.stdout.write("\n")
    sys.exit(0)


def option(name, default=None):
    return args[args.index(name) + 1] if name in args else default


def read_body():
    path = option("--body-file")
    return sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()


def issue_of(number):
    found = state["issues"].get(str(number))
    if found is None:
        fail("GraphQL: Could not resolve to an Issue with the number of %s." % number)
    return found


def view(issue, fields):
    full = dict(issue, labels=[{"name": n} for n in issue["labels"]])
    return {f: full.get(f) for f in fields}


def label_names(value):
    return [v for v in value.split(",") if v]


group, verb = args[0], (args[1] if len(args) > 1 else "")

if group == "repo" and verb == "view":
    out({"url": state["url"]})

if group == "label" and verb == "list":
    out([{"name": n} for n in state["labels"]])

if group == "label" and verb == "create":
    state["labels"].append(args[2])
    state.setdefault("label_colours", {})[args[2]] = option("--color")
    out("created")

if group == "issue" and verb == "list":
    fields = option("--json").split(",")
    wanted = option("--state", "open")
    out([view(i, fields) for i in state["issues"].values() if wanted == "all" or i["state"].lower() == wanted])

if group == "issue" and verb == "create":
    state["creations"] = state.get("creations", 0) + 1
    if state.get("fail_create_at") == state["creations"]:
        fail("error connecting to api.github.com\ncheck your internet connection")
    number = state["next"]
    state["next"] += 1
    issue = {"number": number, "id": 9000 + number, "title": option("--title"), "body": read_body(),
             "labels": [], "state": "OPEN", "stateReason": None}
    for name in label_names(option("--label", "")):
        if name not in state["labels"]:
            fail("could not add label: '%s' not found" % name)
        issue["labels"].append(name)
    state["issues"][str(number)] = issue
    out("https://github.com/o/r/issues/%d" % number)

if group == "issue" and verb == "edit":
    issue_of(args[2])["body"] = read_body()
    out("edited")

if group == "issue" and verb == "close":
    issue = issue_of(args[2])
    issue["state"] = "CLOSED"
    issue["stateReason"] = {"completed": "COMPLETED", "not planned": "NOT_PLANNED"}[option("--reason", "completed")]
    out("closed")

if group == "api":
    path = next(a for a in args[1:] if a.startswith("repos/"))
    method = option("-X", "GET")
    match = re.fullmatch(r"repos/\{owner\}/\{repo\}/issues/(\d+)(?:/(sub_issues|dependencies/blocked_by))?", path)
    if match:
        issue = issue_of(match.group(1))
        kind = match.group(2)
        if kind is None:
            out({"id": issue["id"], "number": issue["number"]})
        key = "sub_issues" if kind == "sub_issues" else "blocked_by"
        if method == "POST":
            wanted = int(option("-F").split("=")[1])
            by_id = {i["id"]: i["number"] for i in state["issues"].values()}
            issue.setdefault(key, []).append(by_id[wanted])
            out({})
        rows = [{"number": n, "state": issue_of(n)["state"].lower()} for n in issue.get(key, [])]
        out([rows] if "--slurp" in args else rows)
fail("fake gh: unsupported call %s" % args)
