#!/usr/bin/env python3
"""Move a 2.x project's docs/backlog/ from `main` onto its GitHub remote's issues (ADR 0055).

Run once per project, from inside its checkout, then delete this script. Standard library only;
it shells out to `gh`. The backlog is read from the `main` branch, never from the working tree.

    migrate-backlog-to-issues.py --dry-run   list every issue it would create; write nothing
    migrate-backlog-to-issues.py             create the issues, then wire and close them; resumable
    migrate-backlog-to-issues.py verify      compare the issues with the files; read-only

An issue carries its old id in its last body line, `Migrated from <old id>, created <date>.`.
That line is the key a rerun skips by and `verify` checks by. Output is plain text to quote in
a pull request; a refusal or a failed check exits 1.
"""
import argparse
import json
import posixpath
import re
import subprocess
import sys
import urllib.parse

BRANCH = "main"
BACKLOG = "docs/backlog/"
NOT_TICKETS = re.compile(r"README\.md|_template\.md|ROADMAP[^/]*\.md")
STATUSES = ("draft", "todo", "in-progress", "in-review", "done")
TYPES = ("feature", "fix", "chore", "spike", "map", "decision")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)
HEADING = re.compile(r"^# (.+?)\s*$", re.M)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
MARKER = re.compile(r"^Migrated from (\S+), created \d{4}-\d{2}-\d{2}\.$")
# The colours ticket-tracker gives a label it creates, so a label made here matches one made there.
LABEL_COLOURS = {"status": "ededed", "type": "c5def5", "context": "bfd4f2"}
# deferred: a list stops at this many issues, with no paging past it, so a larger repository
# would look unmigrated beyond it — page with gh api once a backlog nears it
LIST_LIMIT = "5000"


FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CODE_SPAN = r"(?P<code>(?<!`)(?P<ticks>`+)(?!`)(?:(?!\n[ \t]*\n).)+?(?<!`)(?P=ticks)(?!`))"
LINK = r"(?P<link>\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]*)(?P<title>\s+\"[^\"]*\")?\))"
DEFINITION = r"(?P<definition>^(?P<lead> {0,3}\[[^\]\n]+\]:[ \t]*)(?P<defined>\S+))"
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:|^//")


class Refusal(Exception):
    pass


def git(*args):
    done = subprocess.run(["git", *args], capture_output=True)
    if done.returncode != 0:
        raise Refusal("git %s failed: %s" % (" ".join(args[:2]), done.stderr.decode(errors="replace").strip()))
    return done.stdout


def repository_files():
    return git("ls-tree", "-r", "--name-only", BRANCH).decode("utf-8").splitlines()


class Unreadable(Exception):
    pass


def parse_list(value):
    inner = value.strip()
    if not (inner.startswith("[") and inner.endswith("]")):
        raise Unreadable("blocked_by is not a [A, B] list: %s" % value.strip())
    return [item.strip() for item in inner[1:-1].split(",") if item.strip()]


def parse_ticket(path, raw):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Unreadable("not valid UTF-8 (%s)" % error)
    framed = FRONTMATTER.match(text.replace("\r\n", "\n"))
    if not framed:
        raise Unreadable("no frontmatter between --- lines")
    fields = {}
    for line in framed.group(1).split("\n"):
        key, colon, value = line.partition(":")
        if not colon or not key.strip():
            raise Unreadable("frontmatter line is not `key: value`: %s" % line)
        fields[key.strip()] = value.strip()
    for key in ("id", "status", "context", "type", "created"):
        if not fields.get(key):
            raise Unreadable("frontmatter has no %s" % key)
    name = path[len(BACKLOG):]
    if not name.startswith(fields["id"] + "-"):
        raise Unreadable("id %s is not the start of the file name" % fields["id"])
    if fields["status"] not in STATUSES:
        raise Unreadable("unknown status %s" % fields["status"])
    if fields["type"] not in TYPES:
        raise Unreadable("unknown type %s" % fields["type"])
    if not DATE.fullmatch(fields["created"]):
        raise Unreadable("created is not YYYY-MM-DD: %s" % fields["created"])
    title = HEADING.search(framed.group(2))
    if not title:
        raise Unreadable("no `# ` heading to be the title")
    return {"id": fields["id"], "path": path, "status": fields["status"], "context": fields["context"],
            "type": fields["type"], "created": fields["created"],
            "blocked_by": parse_list(fields["blocked_by"]) if "blocked_by" in fields else [],
            "title": title.group(1), "body": framed.group(2)[title.end():].strip("\n")}


def read_tickets():
    """Every ticket on main, and a refusal line for every file that cannot be one."""
    tickets, problems = [], []
    paths = [p for p in repository_files()
             if p.startswith(BACKLOG) and p.endswith(".md") and "/" not in p[len(BACKLOG):]
             and not NOT_TICKETS.fullmatch(p[len(BACKLOG):])]
    for path in sorted(paths):
        try:
            tickets.append(parse_ticket(path, git("show", "%s:%s" % (BRANCH, path))))
        except Unreadable as reason:
            problems.append("%s: unreadable: %s" % (path, reason))
        except Refusal as reason:
            problems.append("%s: unreadable: %s" % (path, reason))
    return tickets, problems


def map_candidates(tickets):
    """Decision id -> the maps it belongs to: those whose body links it, and those it is blocked_by."""
    by_id = {t["id"]: t for t in tickets}
    rewriter = Rewriter(tickets, {t["id"]: 0 for t in tickets}, repository_files(), "")
    found = {t["id"]: set() for t in tickets if t["type"] == "decision"}
    for ticket in tickets:
        if ticket["type"] != "map":
            continue
        rewriter.seen = set()
        rewriter.rewrite(ticket["body"], ticket["path"])
        for id in rewriter.seen & found.keys():
            found[id].add(ticket["id"])
    for id in found:
        found[id] |= {b for b in by_id[id]["blocked_by"] if b in by_id and by_id[b]["type"] == "map"}
    return {id: sorted(maps) for id, maps in found.items()}


def refusals(tickets, problems):
    by_id = {t["id"]: t for t in tickets}
    found = list(problems)
    for ticket in tickets:
        if ticket["status"] in ("in-progress", "in-review") and ticket["type"] != "map":
            found.append("%s: %s is %s and not a map; finish or park it, and keep no ticket branch open"
                         % (ticket["path"], ticket["id"], ticket["status"]))
    candidates = map_candidates(tickets)
    for ticket in tickets:
        for blocker in ticket["blocked_by"]:
            if blocker not in by_id:
                found.append("%s: %s is blocked_by %s, which is no ticket on %s" % (ticket["path"], ticket["id"], blocker, BRANCH))
        if ticket["type"] == "decision":
            maps = candidates[ticket["id"]]
            if len(maps) != 1:
                found.append("%s: decision %s reaches %s through blocked_by; it needs exactly one"
                             % (ticket["path"], ticket["id"], "no map" if not maps else "%s maps (%s)" % ("two" if len(maps) == 2 else len(maps), ", ".join(maps))))
    return found


def gh(*args, stdin=None):
    try:
        done = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
    except FileNotFoundError:
        raise Refusal("gh is not installed")
    if done.returncode != 0:
        raise Refusal("gh %s failed: %s" % (" ".join(args[:2]), done.stderr.strip()))
    return done.stdout


def gh_json(*args):
    return json.loads(gh(*args) or "null")


def old_id_of(body):
    lines = [line.strip() for line in (body or "").strip().splitlines()]
    found = MARKER.match(lines[-1]) if lines else None
    return found.group(1) if found else None


def migrated_issues():
    """Every issue, open or closed, that carries a marker line: the issues by old id."""
    found = {}
    rows = gh_json("issue", "list", "--state", "all", "--limit", LIST_LIMIT,
                   "--json", "number,body,state,stateReason,labels")
    for row in sorted(rows, key=lambda r: r["number"]):
        old = old_id_of(row["body"])
        if old:
            found.setdefault(old, []).append(row)
    return found


def plan(tickets):
    """What each ticket becomes: its labels, whether it closes, its dependencies and its parent map."""
    by_id = {t["id"]: t for t in tickets}
    planned, candidates = {}, map_candidates(tickets)
    for ticket in tickets:
        labels = ([] if ticket["status"] in ("draft", "done") else ["status:" + ticket["status"]])
        labels += ["type:" + ticket["type"], "context:" + ticket["context"]]
        onto_maps = [b for b in ticket["blocked_by"] if by_id[b]["type"] == "map"]
        planned[ticket["id"]] = {
            "ticket": ticket, "labels": labels, "closed": ticket["status"] == "done",
            "blocked_by": [b for b in ticket["blocked_by"] if b not in onto_maps],
            "dropped": onto_maps, "parent": candidates[ticket["id"]][0] if ticket["type"] == "decision" else None}
    return planned


def marker_line(ticket):
    return "Migrated from %s, created %s." % (ticket["id"], ticket["created"])


def body_of(ticket, text):
    return (text.strip("\n") + "\n\n" if text.strip() else "") + marker_line(ticket) + "\n"


def ambiguous(planned, existing):
    return ["%s is carried by several issues (%s); remove the extras by hand first"
            % (id, ", ".join("#%d" % r["number"] for r in existing[id]))
            for id in planned if len(existing.get(id, [])) > 1]


def ensure_labels(wanted):
    known = {row["name"] for row in gh_json("label", "list", "--json", "name", "--limit", LIST_LIMIT)}
    for name in wanted:
        if name not in known:
            gh("label", "create", name, "--color", LABEL_COLOURS[name.split(":")[0]])
            known.add(name)


def create_issues(planned, existing):
    """Pass 1: one issue per ticket not yet carried by an issue. Returns old id -> number."""
    numbers = {id: rows[0]["number"] for id, rows in existing.items() if id in planned}
    for id, item in planned.items():
        if id in numbers:
            continue
        ensure_labels(item["labels"])
        url = gh("issue", "create", "--title", item["ticket"]["title"], "--body-file", "-",
                 "--label", ",".join(item["labels"]), stdin=body_of(item["ticket"], item["ticket"]["body"])).strip()
        numbers[id] = int(url.rsplit("/", 1)[1])
        print("created #%d for %s" % (numbers[id], id))
    return numbers


class Rewriter:
    """Turns a ticket's links and bare ids into references and blob URLs, outside code."""

    def __init__(self, tickets, numbers, files, repo_url):
        self.by_path = {t["path"]: t for t in tickets}
        self.numbers = numbers
        self.files = set(files)
        self.dirs = {posixpath.dirname(f) for f in files} | {d for f in files for d in parents(f)}
        self.repo_url = repo_url
        self.seen = set()
        ids = sorted(self.numbers, key=len, reverse=True)
        bare = r"(?P<bare>(?<![\w/#-])(?:%s)(?![\w-]))" % "|".join(re.escape(i) for i in ids)
        self.pattern = re.compile("|".join([CODE_SPAN, LINK, DEFINITION, bare]), re.S | re.M)

    def rewrite(self, text, from_path):
        lines, chunk, fence, done = text.splitlines(keepends=True), [], None, []
        for line in lines:
            marker = FENCE.match(line)
            if fence is None and marker:
                done.append(self.inline("".join(chunk), from_path))
                chunk, fence = [], marker.group(1)
                done.append(line)
            elif fence is not None:
                done.append(line)
                if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                    fence = None
            else:
                chunk.append(line)
        done.append(self.inline("".join(chunk), from_path))
        return "".join(done)

    def inline(self, text, from_path):
        return self.pattern.sub(lambda m: self.replacement(m, from_path), text)

    def replacement(self, found, from_path):
        if found.group("code"):
            return found.group(0)
        if found.group("bare"):
            self.seen.add(found.group("bare"))
            return "#%d" % self.numbers[found.group("bare")]
        if found.group("link"):
            target = self.resolve(found.group("target"), from_path)
            if target is None:
                return found.group(0)
            if target[0] == "ticket":
                ticket = self.by_path[target[1]]
                self.seen.add(ticket["id"])
                number = self.numbers[ticket["id"]]
                text = found.group("text").strip().strip("`")
                base = posixpath.basename(ticket["path"])
                if text in ("", ticket["id"], base, base[:-3]):
                    return "#%d" % number
                return "%s (#%d)" % (found.group("text"), number)
            return "[%s](%s%s)" % (found.group("text"), target[1], found.group("title") or "")
        target = self.resolve(found.group("defined"), from_path)
        if target is None:
            return found.group(0)
        if target[0] == "ticket":
            self.seen.add(self.by_path[target[1]]["id"])
        url = "%s/issues/%d" % (self.repo_url, self.numbers[self.by_path[target[1]]["id"]]) \
            if target[0] == "ticket" else target[1]
        return found.group("lead") + url

    def resolve(self, target, from_path):
        """('ticket', path) for a migrated ticket, ('url', url) for another repository path, else None."""
        if not target or target.startswith("#") or SCHEME.match(target):
            return None
        path, _, fragment = target.partition("#")
        path = urllib.parse.unquote(path.partition("?")[0])
        if not path:
            return None
        joined = path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(from_path), path)
        normal = posixpath.normpath(joined)
        if normal == ".." or normal.startswith("../"):
            return None
        anchor = "#" + fragment if fragment else ""
        if normal in self.by_path:
            return ("ticket", normal)
        if normal in self.files:
            return ("url", "%s/blob/%s/%s%s" % (self.repo_url, BRANCH, normal, anchor))
        if normal in self.dirs:
            return ("url", "%s/tree/%s/%s%s" % (self.repo_url, BRANCH, normal, anchor))
        return None


def parents(path):
    found = []
    while "/" in path:
        path = posixpath.dirname(path)
        found.append(path)
    return found


def database_id(number):
    return gh_json("api", "repos/{owner}/{repo}/issues/%d" % number)["id"]


def related(number, kind):
    """The issue numbers already on the other side of a native dependency or sub-issue."""
    pages = gh_json("api", "--paginate", "--slurp", "repos/{owner}/{repo}/issues/%d/%s" % (number, kind))
    return {row["number"] for page in pages for row in page}


def wire(number, kind, field, wanted):
    for other in sorted(wanted - related(number, kind)):
        gh("api", "-X", "POST", "repos/{owner}/{repo}/issues/%d/%s" % (number, kind), "-F", "%s=%d" % (field, database_id(other)))
        print("#%d %s #%d" % (number, "blocked by" if field == "issue_id" else "parent of", other))


def finish_issues(planned, tickets, numbers):
    """Pass 2: rewrite bodies, wire dependencies and sub-issues, close done issues. Safe to rerun."""
    repo_url = gh_json("repo", "view", "--json", "url")["url"]
    rewriter = Rewriter(tickets, numbers, repository_files(), repo_url)
    current = {rows[0]["number"]: rows[0] for rows in migrated_issues().values()}
    for id, item in planned.items():
        number, ticket = numbers[id], item["ticket"]
        wanted = body_of(ticket, rewriter.rewrite(ticket["body"], ticket["path"]))
        if current[number]["body"].strip() != wanted.strip():
            gh("issue", "edit", str(number), "--body-file", "-", stdin=wanted)
            print("rewrote #%d" % number)
    children = {}
    for id, item in planned.items():
        wire(numbers[id], "dependencies/blocked_by", "issue_id", {numbers[b] for b in item["blocked_by"]})
        if item["parent"]:
            children.setdefault(item["parent"], set()).add(numbers[id])
    for parent, wanted in children.items():
        wire(numbers[parent], "sub_issues", "sub_issue_id", wanted)
    for id, item in planned.items():
        if item["closed"] and current[numbers[id]]["state"] != "CLOSED":
            gh("issue", "close", str(numbers[id]), "--reason", "completed")
            print("closed #%d" % numbers[id])


def verify_issues(planned, existing):
    """Compare every ticket with its issue. Returns (problems, issue count)."""
    problems, numbers = [], {}
    for id in planned:
        rows = existing.get(id, [])
        if not rows:
            problems.append("FAIL %s: no issue carries '%s'" % (id, "Migrated from " + id))
        elif len(rows) > 1:
            problems.append("FAIL %s: several issues carry its marker (%s)" % (id, ", ".join("#%d" % r["number"] for r in rows)))
        else:
            numbers[id] = rows[0]["number"]
    named = {number: id for id, number in numbers.items()}

    def call(number):
        return "%s (#%d)" % (named[number], number) if number in named else "#%d" % number

    for id, number in numbers.items():
        row, item = existing[id][0], planned[id]
        head = "FAIL %s (#%d): " % (id, number)
        status = item["ticket"]["status"]
        if item["closed"] != (row["state"] == "CLOSED"):
            problems.append(head + "the file is %s but the issue is %s" % (status, row["state"].lower()))
        elif item["closed"] and row.get("stateReason") != "COMPLETED":
            problems.append(head + "closed as %s, not completed" % row.get("stateReason"))
        have = {label["name"] for label in row["labels"]}
        for family in ("status", "type", "context"):
            kept = {name for name in have if name.startswith(family + ":")}
            wanted = {name for name in item["labels"] if name.startswith(family + ":")}
            problems += [head + "label %s is missing" % name for name in sorted(wanted - kept)]
            problems += [head + "label %s is extra" % name for name in sorted(kept - wanted)]
        wanted = {numbers[b] for b in item["blocked_by"] if b in numbers}
        found = related(number, "dependencies/blocked_by")
        problems += [head + "dependency on %s is missing" % call(n) for n in sorted(wanted - found)]
        problems += [head + "dependency on %s is extra" % call(n) for n in sorted(found - wanted)]
        if item["ticket"]["type"] == "map":
            wanted = {numbers[i] for i, other in planned.items() if other["parent"] == id and i in numbers}
            found = related(number, "sub_issues")
            problems += [head + "sub-issue %s is missing" % call(n) for n in sorted(wanted - found)]
            problems += [head + "sub-issue %s is extra" % call(n) for n in sorted(found - wanted)]
    for old, rows in sorted(existing.items()):
        if old not in planned:
            problems += ["FAIL #%d: carries 'Migrated from %s' but docs/backlog has no file for %s" % (r["number"], old, old)
                         for r in rows]
    return problems, sum(len(rows) for rows in existing.values())


def describe(planned, existing):
    lines, fresh = [], 0
    for id, item in planned.items():
        title = item["ticket"]["title"]
        if id in existing:
            lines.append("%s  exists as #%d, skipped" % (id, existing[id][0]["number"]))
            continue
        fresh += 1
        lines.append("%s  %s" % (id, title))
        lines.append("    labels: " + ", ".join(item["labels"]))
        lines.append("    state: " + ("closed as completed" if item["closed"] else "open"))
        if item["blocked_by"]:
            lines.append("    blocked by: " + ", ".join(item["blocked_by"]))
        if item["parent"]:
            lines.append("    sub-issue of: " + item["parent"])
        if item["dropped"] and not item["parent"]:
            lines.append("    dropped edge onto map: " + ", ".join(item["dropped"]))
    lines.append("")
    lines.append("dry run: would create %d issue%s, skip %d already migrated; wrote nothing"
                 % (fresh, "" if fresh == 1 else "s", len(planned) - fresh))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("verb", nargs="?", choices=("migrate", "verify"), default="migrate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.verb == "verify" and args.dry_run:
        parser.error("verify only reads; --dry-run is for migrate")
    try:
        tickets, problems = read_tickets()
        found = refusals(tickets, problems)
        if found:
            for line in found:
                print("refused: " + line, file=sys.stderr)
            print("%d refusal(s); nothing was written" % len(found), file=sys.stderr)
            return 1
        planned, existing = plan(tickets), migrated_issues()
        found = ambiguous(planned, existing) if args.verb == "migrate" else []
        if found:
            raise Refusal("\n".join(found))
        if args.verb == "verify":
            problems, issue_count = verify_issues(planned, existing)
            print("\n".join(problems))
            if problems:
                print("verify: FAILED, %d problem%s" % (len(problems), "" if len(problems) == 1 else "s"))
                return 1
            print("verify: ok, %d tickets match %d issues" % (len(planned), issue_count))
        elif args.dry_run:
            print(describe(planned, existing))
        else:
            numbers = create_issues(planned, existing)
            finish_issues(planned, tickets, numbers)
    except Refusal as reason:
        print("refused: %s" % reason, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
