# One verb surface for humans, hooks, CI and coding agents, so nothing has to
# reconstruct a build invocation from memory.

SHELL := /bin/bash
MVN   := ./mvnw -B

# Keep an already-correct JAVA_HOME (CI sets one), else find a local JDK 25. A JRE is
# skipped because it looks fine until compilation starts.
JAVAC_OK := $(shell [ -x "$(JAVA_HOME)/bin/javac" ] && "$(JAVA_HOME)/bin/javac" -version 2>&1 | grep -q '^javac 25' && echo yes)
ifneq ($(JAVAC_OK),yes)
JDK25 := $(shell for d in "$$HOME"/.jdks/jdk-25* /usr/lib/jvm/*25*; do [ -x "$$d/bin/javac" ] && echo "$$d" && break; done)
ifneq ($(strip $(JDK25)),)
export JAVA_HOME := $(JDK25)
endif
endif

.DEFAULT_GOAL := help

.PHONY: help doctor build test arch docs fmt lint dup run openapi openapi-check ci clean
.PHONY: fe-install fe-check fe-build openapi-client

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

doctor: ## Check the toolchain before blaming the build
	@bash scripts/doctor.sh

build: ## Compile main sources
	$(MVN) compile

test: ## Run every test, architecture rules included
	$(MVN) test

test-one: ## Run one test class or method, e.g. make test-one T=SomeTest
	@[ -n "$(T)" ] || { echo "T is unset: make test-one T=SomeTest"; exit 1; }
	$(MVN) test -Dtest='$(T)'

arch: ## Run architecture and modularity tests only
	$(MVN) test -Dtest='ArchitectureTest,ModularityTest' -DfailIfNoSpecifiedTests=false

docs: arch ## Regenerate diagrams into target/spring-modulith-docs
	@echo "diagrams written to target/spring-modulith-docs"

fmt: ## Apply formatting
	$(MVN) spotless:apply

lint: ## Verify formatting without touching files
	$(MVN) spotless:check

dup: ## Fail on copy-pasted code
	$(MVN) pmd:cpd-check

config-check: ## Fail on a config comment that explains the tool rather than the choice
	@python3 scripts/check-config-comments.py

adr-check: ## Fail on a duplicate or missing ADR number
	@python3 scripts/check-adr-numbers.py

no-skipped-tests: ## Fail if the last test run skipped anything
	@python3 scripts/check-no-skipped-tests.py

run: ## Start the application
	$(MVN) spring-boot:run

openapi: ## Capture the OpenAPI schema from a running app into docs/openapi.json
	@curl -sf http://localhost:8080/v3/api-docs \
		| python3 -m json.tool --indent 2 --no-ensure-ascii > docs/openapi.json.tmp \
		&& mv docs/openapi.json.tmp docs/openapi.json \
		&& echo "wrote docs/openapi.json" \
		|| { rm -f docs/openapi.json.tmp; echo "app not reachable on :8080 — run 'make run' first"; exit 1; }

openapi-check: ## Fail if the committed schema does not match the running app
	@bash scripts/check-openapi.sh

fe-install: ## Install frontend dependencies
	$(MAKE) -C frontend install

fe-check: ## Typecheck and test the frontend
	$(MAKE) -C frontend check

fe-build: ## Build the frontend bundle
	$(MAKE) -C frontend build

openapi-client: ## Regenerate the typed API client from docs/openapi.json
	$(MAKE) -C frontend openapi-client

ci: lint config-check adr-check test dup ## Everything CI runs for the backend

verify: ## Everything CI runs, backend and frontend, in the order CI runs it
	$(MAKE) ci
	$(MAKE) no-skipped-tests
	$(MAKE) openapi-check
	$(MAKE) fe-check

clean: ## Remove build output
	$(MVN) clean
	$(MAKE) -C frontend clean
