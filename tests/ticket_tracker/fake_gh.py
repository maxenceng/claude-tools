#!/usr/bin/env python3
"""A fake `gh` for the ticket-tracker tests: a JSON file is the whole of GitHub.

FAKE_GH_STATE names the file. Every invocation is appended to its "calls" before anything
else runs, offline or not, so a test can assert on what was attempted as well as on what
changed. "offline" makes every call fail the way gh does without a network, with its text when it is one.
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


def fail(message, code=1):
    save()
    sys.stderr.write(message + "\n")
    sys.exit(code)


def read_file(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def option(name, default=None):
    if name in args:
        return args[args.index(name) + 1]
    return default


def options(name):
    return [args[i + 1] for i, a in enumerate(args) if a == name]


def touch(issue):
    state["clock"] += 1
    issue["updatedAt"] = "2026-10-28T10:00:%02dZ" % state["clock"]


def issue_of(number):
    issue = state["issues"].get(str(number))
    if issue is None:
        fail("GraphQL: Could not resolve to an Issue with the number of %s." % number)
    return issue


def public(issue, fields):
    full = dict(issue)
    full["labels"] = [{"name": n} for n in issue["labels"]]
    return {f: full.get(f) for f in fields}


def labels_in(value):
    return [v for v in value.split(",") if v]


def out(value):
    save()
    sys.stdout.write(value if isinstance(value, str) else json.dumps(value))
    sys.stdout.write("\n")
    sys.exit(0)


if state.get("offline"):
    fail(state["offline"] if isinstance(state["offline"], str)
         else "error connecting to api.github.com\ncheck your internet connection or https://githubstatus.com")

group, verb = args[0], (args[1] if len(args) > 1 else "")

if group == "issue" and verb == "view":
    fields = option("--json").split(",")
    out(public(issue_of(args[2]), fields))

if group == "issue" and verb == "list":
    wanted = option("--state", "open")
    fields = option("--json").split(",")
    rows = [public(i, fields) for i in state["issues"].values()
            if wanted == "all" or i["state"].lower() == wanted]
    out(rows)

if group == "issue" and verb == "edit":
    issue = issue_of(args[2])
    for name in labels_in(option("--add-label", "")):
        if name not in state["labels"]:
            fail("failed to update: '%s' not found" % name)
        if name not in issue["labels"]:
            issue["labels"].append(name)
    for name in labels_in(option("--remove-label", "")):
        if name in issue["labels"]:
            issue["labels"].remove(name)
    body_file = option("--body-file")
    if body_file:
        issue["body"] = read_file(body_file)
    touch(issue)
    out("https://github.com/o/r/issues/%s" % args[2])

if group == "issue" and verb == "create":
    number = state["next"]
    state["next"] += 1
    issue = {"number": number, "id": 9000 + number, "title": option("--title"),
             "body": read_file(option("--body-file")),
             "labels": [], "state": "OPEN", "stateReason": None, "updatedAt": "", "branches": []}
    for name in options("--label"):
        for one in labels_in(name):
            if one not in state["labels"]:
                fail("could not add label: '%s' not found" % one)
            issue["labels"].append(one)
    touch(issue)
    state["issues"][str(number)] = issue
    out("https://github.com/o/r/issues/%d" % number)

if group == "issue" and verb == "close":
    issue = issue_of(args[2])
    issue["state"] = "CLOSED"
    issue["stateReason"] = {"completed": "COMPLETED", "not planned": "NOT_PLANNED"}[option("--reason", "completed")]
    touch(issue)
    out("closed")

if group == "issue" and verb == "develop":
    issue = issue_of(next(a for a in args[2:] if a.isdigit()))
    if "--list" in args:
        out("".join("%s\thttps://github.com/o/r/tree/%s\n" % (b, b) for b in issue["branches"]).rstrip("\n"))
    branch = option("--name") or "%d-%s" % (issue["number"], re.sub(r"[^a-z0-9]+", "-", issue["title"].lower()).strip("-"))
    issue["branches"].append(branch)
    out("github.com/o/r/tree/%s" % branch)

if group == "label" and verb == "list":
    out([{"name": n} for n in state["labels"]])

if group == "label" and verb == "create":
    state["labels"].append(args[2])
    out("created")

if group == "pr" and verb == "create":
    state["prs"].append({"title": option("--title"), "body": read_file(option("--body-file"))})
    out("https://github.com/o/r/pull/%d" % (100 + len(state["prs"])))

if group == "pr" and verb == "list" and "--search" in args:
    term = option("--search").split()[0]
    out([pr for pr in state.get("merged_prs", []) if term in pr["body"]])

if group == "pr" and verb == "list":
    head = option("--head")
    out([{"number": 7} for b in state["merged_heads"] if b == head])

if group == "pr" and verb == "view":
    pull_request = state.get("pull_requests", {}).get(args[2])
    if pull_request is None:
        fail("GraphQL: Could not resolve to a PullRequest with the number of %s." % args[2])
    out({f: pull_request[f] for f in option("--json").split(",")})

if group == "pr" and verb == "edit":
    pull_request = state["pull_requests"][args[2]]
    pull_request["body"] = read_file(option("--body-file"))
    touch(pull_request)
    out("https://github.com/o/r/pull/%s" % args[2])

if group == "pr" and verb == "checks":
    out(state.get("checks", []))

if group == "run" and verb == "view":
    out(state["run_logs"][args[2]])

if group == "api":
    path = next(a for a in args[1:] if a == "graphql" or a.startswith("repos/"))
    method = option("-X", "GET")
    if path == "graphql":
        out(state["graphql"])
    match = re.fullmatch(r"repos/\{owner\}/\{repo\}/issues/(\d+)(?:/(sub_issues|dependencies/blocked_by))?", path)
    if match:
        issue = issue_of(match.group(1))
        kind = match.group(2)
        if kind is None:
            out({"id": issue["id"], "number": issue["number"]})
        key = "sub_issues" if kind == "sub_issues" else "blocked_by"
        if method == "POST":
            wanted = int(option("-F", "").split("=")[1])
            by_id = {i["id"]: i["number"] for i in state["issues"].values()}
            issue.setdefault(key, []).append(by_id[wanted])
            out({})
        rows = [public(issue_of(n), ["number", "title", "state", "stateReason", "labels"]) for n in issue.get(key, [])]
        rows = [{"number": row["number"], "title": row["title"], "state": row["state"].lower(),
                 "state_reason": (row["stateReason"] or "").lower() or None, "labels": row["labels"]} for row in rows]
        page = state.get("page_size", 30)
        pages = [rows[i:i + page] for i in range(0, len(rows), page)] or [[]]
        out(pages if "--slurp" in args and "--paginate" in args else pages[0])
    reply = re.fullmatch(r"repos/\{owner\}/\{repo\}/pulls/(\d+)/comments/(\d+)/replies", path)
    if reply and method == "POST":
        state["replies"].append({"pr": reply.group(1), "comment": reply.group(2), "body": option("-f", "")})
        out({})
fail("fake gh: unsupported call %s" % args)
