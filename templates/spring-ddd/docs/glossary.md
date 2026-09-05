# Ubiquitous language

The words below are the ones that appear in code. If a discussion introduces a new word
for an existing concept, either rename the concept everywhere or add the new word here —
never let two names for one thing coexist.

Keep this file short. A glossary nobody trusts is worse than none.

Add a section per bounded context, and add the term in the same change that introduces
it in code. A glossary updated in a separate pass documents what survived, not what the
words mean.

## <context>

| Term | Meaning | Where it lives |
|---|---|---|
| | | |

## training

Worked example only — see ADR 0008. Delete this section along with the context.

| Term | Meaning | Where it lives |
|---|---|---|
| Course | A course someone can take. Identity and a title; the one thing it doesn't have until a vendor supplies it is `Popularity`. | `training.domain.Course` |
| Popularity | How well-regarded a course is, per the training catalogue vendor — absent until that vendor supplies it, never computed here. | `training.domain.Popularity` |
| Training catalogue | The external vendor whose one field this system consumes, never the other way around. | `training.infrastructure.secondary.client.CourseCatalogueClient` |

## Words we deliberately avoid

| Avoid | Use instead | Why |
|---|---|---|
| Helper, Util, Processor | A name describing what it does | These names hide missing concepts. |
