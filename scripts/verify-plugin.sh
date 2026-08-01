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
commands = set()
command_dir = os.path.join(plugin_root, "commands")
for name in sorted(os.listdir(command_dir)):
    path = os.path.join(command_dir, name)
    checked += 1
    data = frontmatter(path)
    if data is None:
        continue
    commands.add(name[:-3])
    if not data.get("description"):
        fail(path, "missing description — it is what /help shows")

# --- cross references -----------------------------------------------------------------
# A skill or agent named in prose that does not exist is a dead instruction: the agent
# reads it, tries to invoke it, and silently carries on without the conventions.
known = skills | agents
for dirpath, dirnames, filenames in os.walk(plugin_root):
    for name in filenames:
        if not name.endswith(".md"):
            continue
        path = os.path.join(dirpath, name)
        text = open(path, encoding="utf-8").read()
        for ref in re.findall(r"`([a-z][a-z0-9-]+)` (?:skill|agent)", text):
            if ref not in known:
                fail(path, f"refers to `{ref}` skill/agent, which this plugin does not define")

print(f"checked {checked} manifests and documents")
print(f"  agents:   {', '.join(sorted(agents))}")
print(f"  skills:   {', '.join(sorted(skills))}")
print(f"  commands: {', '.join(sorted(commands))}")

if errors:
    print("\nFAIL")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print("\nplugin is well formed")
PY
