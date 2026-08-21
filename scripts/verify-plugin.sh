#!/usr/bin/env bash
# Validate the plugin itself.
#
# CI verifies the scaffolding thoroughly and, until this existed, verified the plugin not
# at all — despite the plugin being the thing people install. A malformed frontmatter key
# or a marketplace entry pointing at a moved directory fails at install time, in someone
# else's session, with an error that does not say which file is wrong.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT" <<'PY'
import json, os, re, sys, yaml

root = sys.argv[1]
errors, checked = [], 0

def fail(path, msg):
    errors.append(f"{os.path.relpath(path, root)}: {msg}")

def frontmatter(path):
    """Return the parsed YAML frontmatter, or None with an error recorded."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(path, "no YAML frontmatter delimited by --- ... ---")
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        fail(path, f"frontmatter is not valid YAML: {e}")
        return None
    if not isinstance(data, dict):
        fail(path, "frontmatter is not a mapping")
        return None
    return data

# --- marketplace and plugin manifests ------------------------------------------------
market_path = os.path.join(root, ".claude-plugin", "marketplace.json")
market = json.load(open(market_path, encoding="utf-8"))
for key in ("name", "plugins"):
    if key not in market:
        fail(market_path, f"missing required key '{key}'")

for entry in market.get("plugins", []):
    checked += 1
    src = os.path.join(root, entry.get("source", ""))
    if not os.path.isdir(src):
        fail(market_path, f"plugin '{entry.get('name')}' source does not exist: {entry.get('source')}")
        continue
    manifest = os.path.join(src, ".claude-plugin", "plugin.json")
    if not os.path.isfile(manifest):
        fail(manifest, "missing plugin.json")
        continue
    plugin = json.load(open(manifest, encoding="utf-8"))
    if plugin.get("name") != entry.get("name"):
        fail(manifest, f"name '{plugin.get('name')}' does not match marketplace entry '{entry.get('name')}'")
    # Without one, an installed copy cannot be told apart from any other and nothing
    # tells someone holding a stale one that it has moved on.
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(plugin.get("version", ""))):
        fail(manifest, f"version '{plugin.get('version')}' is not MAJOR.MINOR.PATCH")

plugin_root = os.path.join(root, "plugins", "ddd-workflow")

# --- agents ---------------------------------------------------------------------------
agents = set()
agent_dir = os.path.join(plugin_root, "agents")
for name in sorted(os.listdir(agent_dir)):
    path = os.path.join(agent_dir, name)
    checked += 1
    data = frontmatter(path)
    if data is None:
        continue
    stem = name[:-3]
    if data.get("name") != stem:
        fail(path, f"frontmatter name '{data.get('name')}' does not match filename '{stem}'")
    agents.add(data.get("name"))
    if not data.get("description"):
        fail(path, "missing description — it is what decides whether the agent is chosen")
    elif len(data["description"]) > 400:
        fail(path, f"description is {len(data['description'])} chars; it sits in the system "
                   "prompt on every request, so keep it under 400")
    if "model" in data and data["model"] not in {"haiku", "sonnet", "opus", "inherit"}:
        fail(path, f"unknown model '{data['model']}'")

# --- skills ---------------------------------------------------------------------------
skills = set()
skill_root = os.path.join(plugin_root, "skills")
for name in sorted(os.listdir(skill_root)):
    path = os.path.join(skill_root, name, "SKILL.md")
    checked += 1
    if not os.path.isfile(path):
        fail(path, "skill directory has no SKILL.md")
        continue
    data = frontmatter(path)
    if data is None:
        continue
    if data.get("name") != name:
        fail(path, f"frontmatter name '{data.get('name')}' does not match directory '{name}'")
    skills.add(data.get("name"))
    if not data.get("description"):
        fail(path, "missing description — it is what decides whether the skill loads")

# --- commands -------------------------------------------------------------------------
# A command that dispatches to a directory of steps keeps the same list in three places:
# the verbs named in its prose, the files on disk, and the argument-hint a human reads in
# the picker. They are edited in different places and have already drifted — `refine`
# shipped as a step and a dispatch verb while the hint still advertised five verbs, so the
# one command that tells you to run it was the one place you could not discover it.
DISPATCH = re.compile(r"one of (.+?)\s*—\s*by reading", re.S)
VERB = re.compile(r"`([a-z][a-z0-9-]*)`")


def check_steps(path, stem, steps_dir, data):
    """Reconcile a command's dispatch verbs, its step files and its argument-hint."""
    prose = open(path, encoding="utf-8").read()
    dispatch = DISPATCH.search(prose)
    if not dispatch:
        fail(path, f"has a {stem}-steps/ directory but no 'one of `a`, `b` — by reading' "
                   "line naming the verbs it dispatches on")
        return set()

    verbs = set(VERB.findall(dispatch.group(1)))
    files = {n[:-3] for n in os.listdir(steps_dir) if n.endswith(".md")}

    for missing in sorted(verbs - files):
        fail(path, f"dispatches on '{missing}' but {stem}-steps/{missing}.md does not exist")
    for orphan in sorted(files - verbs):
        fail(os.path.join(steps_dir, f"{orphan}.md"),
             f"is a step {stem}.md never dispatches to — add it to the verb list or delete it")

    hint = data.get("argument-hint") or ""
    if not hint:
        fail(path, "dispatches on verbs but has no argument-hint, so the picker shows none of them")
    else:
        for unadvertised in sorted(v for v in verbs & files if not re.search(rf"\b{re.escape(v)}\b", hint)):
            fail(path, f"dispatches on '{unadvertised}' but the argument-hint does not "
                       "mention it, so nothing tells a human the verb exists")

    return verbs & files


commands = set()
steps = {}
command_dir = os.path.join(plugin_root, "commands")
for name in sorted(os.listdir(command_dir)):
    path = os.path.join(command_dir, name)
    checked += 1
    data = frontmatter(path)
    if data is None:
        continue
    stem = name[:-3]
    commands.add(stem)
    if not data.get("description"):
        fail(path, "missing description — it is what /help shows")

    steps_dir = os.path.join(plugin_root, f"{stem}-steps")
    if os.path.isdir(steps_dir):
        checked += 1
        found = check_steps(path, stem, steps_dir, data)
        if found:
            steps[stem] = found

# --- cross references -----------------------------------------------------------------
# A skill or agent named in prose that does not exist is a dead instruction: the agent
# reads it, tries to invoke it, and silently carries on without the conventions.
#
# Reusing another plugin's skill is deliberate rather than a mistake — the README says to
# check what `superpowers` and the review plugins already provide before adding anything
# here. So a reference carrying a `plugin:` prefix is accepted as an external dependency
# and reported below. What is not accepted is a bare name this plugin does not define:
# unqualified, there is no way to tell a deliberate reuse from a typo, and both fail the
# same silent way at runtime.
known = skills | agents
external = set()
for dirpath, dirnames, filenames in os.walk(plugin_root):
    for name in filenames:
        if not name.endswith(".md"):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8").read()
        for ns, ref in re.findall(r"`(?:([a-z][a-z0-9-]+):)?([a-z][a-z0-9-]+)` (?:skill|agent)", text):
            if ns:
                external.add(f"{ns}:{ref}")
            elif ref not in known:
                fail(
                    path,
                    f"refers to `{ref}` skill/agent, which this plugin does not define — "
                    f"qualify it as `<plugin>:{ref}` if another plugin owns it",
                )

print(f"checked {checked} manifests and documents")
print(f"  agents:   {', '.join(sorted(agents))}")
print(f"  skills:   {', '.join(sorted(skills))}")
print(f"  commands: {', '.join(sorted(commands))}")
for stem, verbs in sorted(steps.items()):
    print(f"  {stem} steps: {', '.join(sorted(verbs))}")
if external:
    print(f"  external: {', '.join(sorted(external))}")
    print("            these must be installed separately; nothing reports it if they are not")

if errors:
    print("\nFAIL")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print("\nplugin is well formed")
PY
