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

---

## 3. Start a new project

The plugin assumes scaffolding — `make` targets, `ArchitectureTest`, `docs/glossary.md`,
the error kernel. A bare `spring init` has none of it, and the agents will confidently
reference commands that do not exist. So start from the template:

Build and install the archetype once per machine. The archetype is generated from the
template rather than committed, so this step is also what a fresh clone needs:

```bash
git clone git@github.com:maxenceng/claude-tools.git
cd claude-tools
./scripts/build-archetype.sh
mvn -f templates/spring-ddd-archetype/pom.xml clean install
```

Then generate as many projects as you like:

```bash
mvn archetype:generate \
  -DarchetypeGroupId=dev.maxenceng \
  -DarchetypeArtifactId=spring-ddd-archetype \
  -DarchetypeVersion=1.0.0-SNAPSHOT \
  -DgroupId=com.acme -DartifactId=billing -Dpackage=com.acme.billing \
  -DinteractiveMode=false

cd billing && git init
```

Nothing needs renaming. The package directories, every `package` and `import`
declaration, `ArchitectureTest`'s scanned package, the pom coordinates and
`spring.application.name` are all set from those three properties.

Verify before writing a line of your own:

```bash
make doctor     # toolchain
make ci         # lint, tests, duplication
make fe-check   # frontend typecheck and tests
```

All three pass on a fresh copy. If they do not, fix that first — debugging scaffolding
and a new domain model at the same time is how people end up abandoning the scaffolding.

Then delete `src/test/resources/archunit.properties`. It exists only so the architecture
rules tolerate a project with no bounded context; once you have one, you want the strict
default back, because a rule that suddenly matches nothing is telling you something.

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
/ticket                    # the board: what is todo, in progress, in review
/ticket new <description>  # writes a ticket, forces the context and model questions
/ticket start TRAIN-42     # branch, then implement test-first
/ticket review TRAIN-42    # make ci, architecture review, code review, PR
/ticket done TRAIN-42      # after merge; notes, retro, ADR if warranted
```

Between `start` and `review` you mostly read and answer questions. That is the intended
shape, not a sign something is wrong.

Open `docs/backlog/` as an Obsidian vault for a board view. Nothing depends on Obsidian —
the files are plain markdown, and `/ticket` reads and writes them directly.

---

## 6. Where you decide

Everything below is a judgement no test can make. The rest of the system is built so that
it fails loudly without you.

**The model decision on every ticket.** New behaviour on an existing aggregate, a new
aggregate, or a new context? `/ticket start` refuses to run without it. This is the most
expensive thing to get wrong and the only one nothing can check.

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

1. `com.example.<app>.<context>` with a `package-info.java` carrying `@ApplicationModule`.
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

### Handle duplication

`/find-duplication`. Not every duplicate should be merged — two blocks that look alike but
change for different reasons should stay apart. Never extract across a context boundary.

---

## 8. What to read

Yours, and it is about five minutes of material:

- `CLAUDE.md` — the hard rules, deliberately short
- `docs/glossary.md` — the words
- `docs/context-map.md` — the contexts
- `docs/adr/` — why things are as they are
- `docs/backlog/` — what is in flight

Not yours: `skills/ddd-backend/SKILL.md`, ~390 lines written for the agent. That
asymmetry is the design — prose for the machine, enforcement for the build, a small
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

`make doctor` first whenever the build looks wrong before your change should have touched
it. It checks the toolchain, which is the usual culprit.

---

## 10. Limits

Worth knowing before you rely on any of it.

**The plugin assumes this project shape.** On something different, `ddd-backend` names
types and `make` targets that do not exist. Install it, then delete or rewrite that skill
rather than letting it answer confidently and wrongly. `project-retro`,
`architecture-reviewer` and `codebase-explorer` travel fine.

**The archetype is generated, not hand-maintained.** `templates/spring-ddd` is the
readable, buildable source; `scripts/build-archetype.sh` derives the archetype from it.
Edit the template, re-run the script, `mvn install`. Never edit anything under
`templates/spring-ddd-archetype/`.

**The template's `ArchitectureTest` is still a copy** of claude-learning's. Nothing
detects divergence between those two yet.

**Keep claude-learning green.** It is the template's source and the skill's reference.
The skill contradicted it in five places precisely because nobody had run both against
each other.

**No ticket-tracker integration.** Tickets are pasted in. A Jira or Linear MCP server
would close that; the ticket format would not change.
