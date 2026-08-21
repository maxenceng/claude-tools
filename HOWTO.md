# How to use this

`README.md` says what this toolkit *is*. This says how to work with it.

Written for the person driving, not for the agent. The surface you touch is small on
purpose: anything mechanical either fails the build or is done for you, and what is left
is judgement.

---

## 1. Which situation are you in

| | Do this |
|---|---|
| Starting a new project | [Start from the template](#3-start-a-new-project) |
| Existing project, same shape | [Install the plugin](#4-add-the-toolkit-to-an-existing-project), then `/onboard` |
| Existing project, different shape | Install it, then delete or rewrite `ddd-backend` — see [limits](#10-limits) |
| Just want to work a ticket | [The daily loop](#5-the-daily-loop) |

---

## 2. One-time, per machine

```bash
/plugin marketplace add maxenceng/claude-tools
```

The marketplace is `maxence-tools`; the plugin inside it is `ddd-workflow`.

If you forked, use `<your-owner>/<your-repo>` instead. Everything below works the same
from a fork, with one thing to change: the archetype's coordinates are `dev.maxenceng`
in `scripts/build-archetype.sh` and `scripts/new-ddd-project.sh`. Change both together
or generation stops resolving — `scripts/verify-archetype.sh` will tell you if you miss
one.

---

## 3. Start a new project

The plugin assumes scaffolding — `make` targets, `ArchitectureTest`, `docs/glossary.md`,
the error kernel. A bare `spring init` has none of it, and the agents will confidently
reference commands that do not exist. So start from the template:

Build and install the archetype once per machine. The archetype is generated from the
template rather than committed, so this step is also what a fresh clone needs:

```bash
git clone https://github.com/maxenceng/claude-tools.git
cd claude-tools
./scripts/build-archetype.sh
mvn -f templates/spring-ddd-archetype/pom.xml clean install
```

Put the wrapper on your PATH once — anywhere on your `PATH` works, `~/.local/bin` is
just a common choice:

```bash
ln -s "$PWD/scripts/new-ddd-project.sh" ~/.local/bin/new-ddd-project
```

Then generate as many projects as you like, from anywhere:

```bash
new-ddd-project com.acme billing
cd billing && git init
```

The package defaults to `<groupId>.<artifactId>` with hyphens removed, since a hyphen is
legal in an artifactId and not in a Java package — `billing-service` gives
`com.acme.billingservice`. Pass a third argument to override it.

Generation resolves the archetype from `~/.m2`, so this needs no path to the clone. It
refuses to run inside an existing Maven project, which otherwise succeeds and buries the
new project inside the old one.

Without the wrapper, the underlying command is:

```bash
mvn archetype:generate \
  -DarchetypeGroupId=dev.maxenceng \
  -DarchetypeArtifactId=spring-ddd-archetype \
  -DarchetypeVersion=1.0.0-SNAPSHOT \
  -DgroupId=com.acme -DartifactId=billing -Dpackage=com.acme.billing \
  -DinteractiveMode=false
```

Nothing needs renaming. The package directories, every `package` and `import`
declaration, `ArchitectureTest`'s scanned package, the pom coordinates and
`spring.application.name` are all set from those three properties.

Verify before writing a line of your own:

```bash
make doctor      # toolchain
make fe-install  # frontend dependencies, once
make verify      # everything CI runs, backend and frontend, in CI's order
```

All three pass on a fresh copy. If they do not, fix that first — debugging scaffolding
and a new domain model at the same time is how people end up abandoning the scaffolding.

Then delete `src/test/resources/archunit.properties`. It exists only so the architecture
rules tolerate a project with no bounded context; once you have one, you want the strict
default back, because a rule that suddenly matches nothing is telling you something.

And write the `## What this is` brief at the top of `CLAUDE.md`, replacing the four
prompts it ships with. Everything else in a generated project describes how to build;
that section is the only thing saying what is being built, and without it an agent will
infer a purpose from the code and be confidently wrong about scope. `make doctor` reports
it as unwritten until you replace it. Keep it to the length it arrives at — the file is
read on every request.

---

## 4. Add the toolkit to an existing project

```bash
/plugin install ddd-workflow@maxence-tools
```

Then `/onboard`. It reads the project through the `codebase-explorer` agent, regenerates
the architecture diagrams, and reports where the code and the documentation disagree.
Run it again whenever you come back to a project after a few weeks.

---

## 5. The daily loop

Tickets are markdown in `docs/backlog/` with YAML frontmatter. Status changes ride along
in the branch and the PR that caused them, so "what state was this in when we merged" is
a question history answers.

```
/ticket                     # the board: what is draft, todo, in progress, in review
/ticket new <description>   # capture only: one draft per line, asks almost nothing
/ticket refine BILLING-14   # the questions, the model decision, the criteria
/ticket start BILLING-14    # branch, then implement test-first
/ticket review BILLING-14   # make verify, architecture review, code review, PR
/ticket respond BILLING-14  # act on PR comments; repeat as often as needed
/ticket done BILLING-14     # after merge; notes, retro, ADR if warranted

/debt                       # the ledger: limits this project chose to live with
/find-duplication           # copy-pasted code, and whether it is worth extracting
/onboard                    # re-read the project and refresh its architecture docs
```

`new` and `refine` are deliberately two verbs. `new` captures — one draft per line of the
argument, in the words they were given in, asking nothing about design. `refine` is where
the questioning, the model decision and the acceptance criteria happen, one ticket at a
time, and it is what moves a `draft` to `todo`. `start` refuses a `draft`, so nothing
skips it. Writing a backlog down and deciding six designs are separate sittings, which is
the whole point of the split.

`respond` is the one that repeats. Leave comments on the PR — inline on a line is best,
since the file and line come along with the text — then run it. It collects every comment
endpoint, checks each item against the code before implementing it, commits the answer as
one change and pushes, then re-verifies the acceptance criteria the change touched and
replies in each thread saying what changed or why nothing did. Disagreeing with a comment
is a valid outcome and gets written down.

It pushes before re-verifying on purpose: CI starts services and boots the application, so
it demonstrates criteria a local shell often cannot, and waiting for it beats unticking a
box the pipeline is about to prove.

The prefix is the bounded context the work sits in, so a ticket you cannot prefix is
usually two tickets — or a context you have not named yet. Either is worth discovering
before the code, which is the whole reason the prefix is not free-form.

Between `start` and `review` you mostly read and answer questions. That is the intended
shape, not a sign something is wrong.

Of everything here this is the least exercised part, and unlike the template and the
archetype nothing in CI can check it — a command is prose, and prose only fails when a
person runs it. Read what it proposes before agreeing, at least for the first few.

Open `docs/backlog/` as an Obsidian vault for a board view. Nothing depends on Obsidian —
the files are plain markdown, and `/ticket` reads and writes them directly.

---

## 6. Where you decide

Everything below is a judgement no test can make. The rest of the system is built so that
it fails loudly without you.

**The model decision on every ticket.** New behaviour on an existing aggregate, a new
aggregate, or a new context? `/ticket refine` is where it is made and `/ticket start`
refuses to run without it. This is the most expensive thing to get wrong and the only one
nothing can check.

**Which word wins.** Once a term is in `docs/glossary.md` the code follows. Before that,
two names for one concept quietly split the model in half.

**What a failing architecture rule means.** Usually the code is wrong. Occasionally the
rule is. Choosing "the rule is wrong" means writing an ADR — which is the point: it makes
reversing a decision deliberate rather than convenient.

**Which review findings to accept.** The reviewers are advisory, and are meant to be
argued with.

**Scope.** An agent will keep building. Deciding what *not* to do stays yours.

---

## 7. Recipes

### Add a bounded context

1. `<your root package>.<context>` with a `package-info.java` carrying `@ApplicationModule`.
2. `domain`, `application`, `infrastructure.primary`, `infrastructure.secondary` beneath it.
3. Expose to other contexts from the context **root** package only.
4. Add its row to `docs/context-map.md` and its terms to `docs/glossary.md`, in this change.
5. `make arch`.

Most of the shape is enforced rather than advised, so run the tests and read the failures
instead of checking a list by eye.

### Change the API

Change the controller, then recapture — three steps, and skipping to the last is the
standard way the frontend silently breaks:

```bash
make run              # in another shell
make openapi          # writes docs/openapi.json
make openapi-client   # writes the typed client
```

Commit `docs/openapi.json`. `@ApiResponse` codes are the contract; check them against
`GlobalExceptionHandler` rather than guessing, and never document a code no handler emits.

### Rename a domain word

Glossary first, then code, then the displaced word into the "words we deliberately avoid"
table with the reason. Doing it in that order means the reason survives; doing it in the
other order means only the diff does.

### Record a limit you chose to live with

A guard covering one column of two, a one-second window left open, a query proved only
where Docker runs. Mark it where you made it:

```java
// deferred: the condition names the hashed password only, so a write that moves the floor
// alone is unguarded — name the floor too once "log out everywhere" exists
```

Ceiling first, then the trigger. A marker with no trigger is the kind that rots, because
nothing will ever say it is time. `/debt` sweeps these together with ADR *Consequences* and
ticket *Notes* into one ledger, and tags the ones with no trigger — those are the rows
worth reading twice.

A limit nobody decided on is not debt, it is an oversight. Raise it as one.

### Handle duplication

`/find-duplication`. Not every duplicate should be merged — two blocks that look alike but
change for different reasons should stay apart. Never extract across a context boundary.

---

## 8. What to read

Yours, and it is about five minutes of material:

- `CLAUDE.md` — what this project is, and the hard rules; deliberately short
- `docs/glossary.md` — the words
- `docs/context-map.md` — the contexts
- `docs/adr/` — why things are as they are
- `docs/backlog/` — what is in flight

Not yours: `skills/ddd-backend/SKILL.md`, several hundred lines written for the agent.
That asymmetry is the design — prose for the machine, enforcement for the build, a small
honest surface for you.

---

## 9. When something breaks

| Symptom | Cause | Fix |
|---|---|---|
| `make lint` fails on import order | Spotless is stricter than your editor | `make fmt` |
| `release version 25 not supported` | `mvn`/`./mvnw` called directly | Use `make` — it selects the JDK |
| ArchUnit: *failed to check any classes* | A rule matches nothing | In a fresh template, expected. Anywhere else, something was renamed out from under it |
| A frontend field is `undefined`, but typed | Client generated from a stale schema | Full three-step recapture |
| `npm ci` fails | No lockfile | Commit `package-lock.json` |
| `@WebMvcTest` will not resolve | Boot 4 moved the MVC slice | Add `spring-boot-webmvc-test` |
| Tests pass but you do not believe them | Possibly justified | Break the code and watch the test fail |
| CI says the schema is stale | Backend changed, nobody recaptured | `make run`, `make openapi`, `make openapi-client` |
| `make ci` green, CI red | `make ci` is the backend job's first step only | `make verify` — it runs the whole pipeline, in the pipeline's order |
| `make verify` green, CI red | The two have drifted apart | A defect in the `Makefile`, not a step to run by hand. Fix `verify` so it matches the workflow again |
| A `/ticket` step silently does nothing | It names a skill from `superpowers` that is not installed | `/plugin install superpowers@claude-plugins-official` |

`make doctor` first whenever the build looks wrong before your change should have touched
it. It checks the toolchain, which is the usual culprit.

---

## 10. Limits

Worth knowing before you rely on any of it.

**The plugin assumes this project shape.** On something different, `ddd-backend` names
types and `make` targets that do not exist. Install it, then delete or rewrite that skill
rather than letting it answer confidently and wrongly. `project-retro`,
`architecture-reviewer` and `codebase-explorer` travel fine.

**`/ticket` leans on `superpowers`, and fails quietly without it.** `refine` invokes
`superpowers:brainstorming`, `respond` invokes `superpowers:receiving-code-review`, and
`review` invokes `superpowers:verification-before-completion`; the general code review
goes to `code-review` or `pr-review-toolkit`. Reusing those rather than reimplementing them is deliberate, but a
named skill that is not installed does not announce itself — the step simply proceeds
without it, and the result looks like the command being loose rather than a missing
dependency. Install `superpowers` alongside this, or expect those steps to be advisory.

**The archetype is generated, not hand-maintained.** `templates/spring-ddd` is the
readable, buildable source; `scripts/build-archetype.sh` derives the archetype from it.
Edit the template, re-run the script, `mvn install`. Never edit anything under
`templates/spring-ddd-archetype/`.

**The archetype is installed, not published.** `mvn install` puts it in your own `~/.m2`,
so it exists on the machine that built it and nowhere else. That is fine for one person
and not fine for a team: everyone runs the clone-and-install above, and nothing tells
them when the template has moved on. Deploying the archetype to a shared repository is
the fix, and this toolkit does not do it for you.

**Dependencies are pinned and unwatched.** The template fixes Spring Boot, Java and the
frontend toolchain at the versions it was written against, with no Dependabot or Renovate
configuration. A project generated a year from now starts a year behind.

**Verify before pushing.** `./scripts/verify-plugin.sh` checks the manifests and
frontmatter; `./scripts/verify-archetype.sh` generates a project, builds both halves, and
generates again through the wrapper. CI runs both, plus the template's own suite.

**Prose is the part that rots.** The build catches a broken archetype, a stale schema and
a violated boundary. It cannot catch a skill recommending a method that does not exist,
which had happened here and was found by reading rather than by CI. When a document and
the code disagree, the code is the one that ran.

**No ticket-tracker integration.** Tickets are pasted in. A Jira or Linear MCP server
would close that; the ticket format would not change.
