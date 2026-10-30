# 19. The docs build on a pinned Zensical from a mkdocs.yml both tools read, and deploy only when enabled

Date: 2026-10-30

## Status

Accepted.

## Context

`docs/` holds the glossary, the context map, the ADRs and, later, research and endpoint maps. They read fine on GitHub,
but they are not a site, and nothing checks that one page's link still reaches another. MkDocs 1.x has stalled, and Material for
MkDocs is in maintenance mode until 2027-05-05. Its maintainers' successor is Zensical, which is 0.x, changes every few
days, and silently ignores a plugin it does not know.

## Decision

- **Zensical builds the site, pinned in one Makefile variable.** `make docs` runs `uvx zensical==$(ZENSICAL_VERSION)`,
  currently 0.0.73. A bump is an edit to that variable, made on purpose and checked by the strict build. Rejected: an
  unpinned `uvx zensical`, which changes behaviour on days nobody touched the pipeline; MkDocs with Material, which
  reaches end of life in 2027 and would mean a migration later.
- **`mkdocs.yml` holds no plugin, only settings Zensical reads or skips harmlessly.** That keeps MkDocs 1.x with Material
  as a fallback while Zensical is 0.x. An unlisted plugin is dropped without an error, so none is listed. `validation`
  is read by MkDocs alone; Zensical checks links and anchors without it. There is no `nav:`, so the filesystem is the one
  source of the site's structure. Rejected: `zensical.toml`, which MkDocs cannot read.
- **The build is strict.** `strict: true` turns a link to a missing page or a missing anchor into a failed build.
  `make verify` runs `make docs` after `make ci`, and so does CI. Links to a directory are not checked, so the landing
  page links pages.
- **`docs/README.md` is the home page.** Zensical takes a `README.md` as a section index, so GitHub shows the same file.
- **The Spring Modulith diagrams are `make diagrams`**, into `target/spring-modulith-docs/`, so `make docs` means the
  site in every project that uses this harness.
- **Deploying to GitHub Pages is a separate workflow.** It runs on a push to `main`, and only when the repository
  variable `DOCS_PAGES` is `true`. Without that variable, every pull request still builds and checks the site, but
  nothing is published. This keeps a repository that has not enabled Pages from failing on every merge.
  Rejected: deploying unconditionally.
- **`site/` is build output and gitignored.**

## Consequences

- `uv` is a build prerequisite, and `make doctor` reports it.
- External links are not checked.
- Zensical's cache is not cached in CI, because its docs advise against it while the cache format changes.
- A plugin added to `mkdocs.yml` later has to be checked against Zensical's supported list by hand.
- An `.html` endpoint diagram under `docs/endpoints/` is copied into the site as a static file, not rendered as a page.
