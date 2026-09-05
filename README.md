# claude-tools

Shared Claude Code configuration for personal projects, packaged as a plugin so it is
installed by reference rather than copied. Copied `.claude/` folders drift apart within
a couple of projects; this does not.

Lives at [maxenceng/claude-tools](https://github.com/maxenceng/claude-tools). CI builds
the template and, separately, generates a project from the archetype and builds that —
because the archetype can stop copying a file without the template ever noticing.

After cloning, run `./scripts/build-archetype.sh` once: the archetype is generated from
the template rather than committed, so that a second hand-editable copy cannot exist.

**[HOWTO.md](HOWTO.md)** is the working guide: starting a project, the ticket loop, where
your judgement is actually needed, recipes, and what to do when something breaks. This
file covers what the toolkit is; that one covers how to use it.

## Two layers

`plugins/` is the **advice** layer — agents, skills, commands, installed by reference.

`templates/spring-ddd/` is the **scaffolding** layer the advice assumes. The plugin's
files reference `make test`, `make arch`, `ArchitectureTest`, `docs/glossary.md` and the
error kernel; none of those exist in a bare `spring init`, so installing the plugin into
an unscaffolded project gives confident answers about commands that are not there.

Start new projects from the template, then install the plugin. They live in one repo so
they cannot drift apart — which is exactly how the skill came to contradict the worked
example before.

## Install into a project

```bash
# once per machine
/plugin marketplace add maxenceng/claude-tools

# once per project
/plugin install ddd-workflow@maxence-tools
```

## What it provides

### Agents

| Agent | Purpose | Model |
|---|---|---|
| `codebase-explorer` | Reads widely, reports briefly. Keeps exploration out of the main context. | haiku |
| `backend-ddd` | Backend features inside a bounded context. | opus |
| `frontend` | React/TypeScript against the generated API client. | sonnet |
| `devops` | CI, containers, build tooling. | sonnet |
| `architecture-reviewer` | Modelling review only — boundaries, invariants, vocabulary. | opus |

There is deliberately **no general code reviewer** here. The `code-review` and
`pr-review-toolkit` plugins already provide several, and a fourth would add confusion
rather than coverage. `architecture-reviewer` covers only what those cannot: whether
the change fits the domain model.

### Skills

- `ddd-backend` — conventions for aggregates, ports, adapters, error handling, the
  OpenAPI contract, tests and comments. Loaded when writing backend code, not on every
  request.
- `project-retro` — turns repeated work, repeated corrections, and duplicated code into
  build checks, Make targets, hooks or skills.

### Commands

- `/ticket` — work a backlog ticket end to end: capture, refine, start, review, respond
  to feedback, close. Capture and analysis are separate verbs on purpose: `new` writes a
  `draft` per line and asks almost nothing, `refine` is where the questions, the modelling
  and the acceptance criteria happen and the ticket becomes `todo`. That split is what
  lets a whole backlog be written in one sitting without deciding six designs at once.
  Tickets are markdown in `docs/backlog/`, so status changes ride along in the branch and
  the PR that caused them. Open the folder as an Obsidian vault for a board; nothing
  depends on it. Each step names the agent or skill that owns it, so the reviewers are
  dispatched rather than suggested.
- `/onboard` — understand a project and refresh its architecture docs.
- `/find-duplication` — run the duplication detectors and propose extractions worth making.
- `/debt` — collect the limits this project chose to live with, from `deferred:` markers in
  code, ADR *Consequences* and ticket *Notes*, into one ledger. A deferral written down in
  three places is written down nowhere.

### Template and archetype

`templates/spring-ddd/` — Spring Boot 4 / Java 25 with hexagonal layering and a typed
React frontend, containing one minimal worked-example context (`training`, ADR 0008 in the
template) and no other business logic. This is the readable, buildable source:
`make verify` — the whole pipeline — passes on it directly. Keep it that way, because
scaffolding that fails on first run gets deleted rather than fixed.

`templates/spring-ddd-archetype/` — a Maven archetype **generated from** that template by
`scripts/build-archetype.sh`. It is what you actually start projects from, because it
sets the package, coordinates and application name for you rather than leaving a rename
to be done by hand and half-finished.

Edit the template, re-run the script, `mvn install`. Never edit the archetype directly —
it is build output, and one source of truth is the whole point.

`scripts/new-ddd-project.sh com.acme billing` wraps the generate command. Symlink it onto
your PATH and it works from any directory, since the archetype resolves from `~/.m2`.

## Design rules for anything added here

**Push each rule to the cheapest layer that can enforce it.** A rule an ArchUnit test
can check should be a test, not a sentence in an agent prompt. Tests fail; prose is
advisory and is re-read on every request whether relevant or not.

**Keep agent descriptions short.** Every description sits in the system prompt on every
request across every project. The body can be long — it loads only on invocation.

**Prefer skills to CLAUDE.md.** CLAUDE.md is always resident. A skill costs nothing
until it is needed.

**Do not duplicate an installed plugin.** Check what `code-review`, `pr-review-toolkit`
and `superpowers` already provide before adding something here.

**Depending on one is fine; depending silently is not.** `/ticket` invokes
`superpowers:brainstorming`, `superpowers:receiving-code-review` and
`superpowers:verification-before-completion`, and sends its general code review to
`code-review` or `pr-review-toolkit`. That is the rule above working as intended — but
those steps do nothing if the plugin is absent, and nothing reports it at runtime. Qualify
an outside reference with its plugin: `verify-plugin.sh` accepts a `plugin:` prefix as a
declared dependency and lists it, and rejects a bare name this plugin does not define,
because unqualified there is no way to tell deliberate reuse from a typo.
